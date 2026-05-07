# -- AI info --
# Me: Core cog functionality
# AI (GPT-5.2-Codex): Caching system (based on pseudocode I provided)

import icmplib
import ipaddress
import discord
from discord.ext import commands
import logging
import socket
import requests
import json
import pathlib
import time
from typing import TypedDict
from modules.embeds import send_error, send_info, send_success, send_warning
from modules.permission import requires_admin


logger = logging.getLogger("goober")


class IPAddress(str):
    def __new__(cls, value: str) -> 'IPAddress | None':
        try:
            if icmplib.is_ipv6_address(value):
                raise ValueError("IPv6 addresses are not supported yet.")
            if not icmplib.is_ipv4_address(value):
                raise ValueError(f"Invalid IPv4 address: {value}")

            temp_ipv4 = ipaddress.IPv4Address(value)
            if (
                temp_ipv4.is_multicast
                or temp_ipv4.is_reserved
                or temp_ipv4.is_loopback
                or temp_ipv4.is_unspecified
                or not temp_ipv4.is_private
            ):
                raise ValueError(f"IP address {value} is not a valid local IPv4 address.")

            return super().__new__(cls, value)
        except Exception:
            logger.exception("Error creating IPAddress")
            return None


class LanCache(TypedDict):
    ips: dict[str, dict[str, str]]
    aliases: dict[str, str]


class LAN(commands.Cog):
    CACHE_TTL_SECONDS = 604_800  # 1 week

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "🌐 | Commands for LAN device info"
        self.cache = pathlib.Path(__file__).parent.parent.parent / "data" / "lan_cache.json"

    def _ping_device(self, ip: IPAddress, ping_count: int = 1) -> icmplib.Host | None:
        try:
            return icmplib.ping(ip, count=ping_count, timeout=2, privileged=False)
        except Exception:
            logger.exception(f"Error pinging {ip}")
            return None

    def _load_cache(self) -> LanCache:
        cache: LanCache = {
            "ips": {},
            "aliases": {},
        }

        try:
            with open(self.cache, "r") as cf:
                loaded = json.load(cf)
            if isinstance(loaded, dict):
                loaded_ips = loaded.get("ips", {})
                if isinstance(loaded_ips, dict):
                    for ip_key, entry in loaded_ips.items():
                        if not isinstance(entry, dict):
                            continue
                        cache["ips"][str(ip_key)] = {str(k): str(v) for k, v in entry.items()}

                loaded_aliases = loaded.get("aliases", {})
                if isinstance(loaded_aliases, dict):
                    for alias, ip_value in loaded_aliases.items():
                        if not isinstance(alias, str) or not isinstance(ip_value, str):
                            continue
                        cache["aliases"][alias] = ip_value
        except FileNotFoundError:
            return cache
        except Exception:
            logger.exception("Error loading LAN cache")

        return cache

    def _save_cache(self, cache: LanCache) -> None:
        self.cache.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.cache, "w") as cache_file:
                json.dump(obj=cache, fp=cache_file, indent=4, sort_keys=True)
        except Exception:
            logger.exception("Error saving LAN cache")

    def _is_stale(self, entry: dict[str, str]) -> bool:
        try:
            updated_at = int(entry.get("updated_at", "0"))
        except ValueError:
            updated_at = 0
        return (int(time.time()) - updated_at) > self.CACHE_TTL_SECONDS

    def _update_cache_entry(
        self,
        cache: LanCache,
        ip: str,
        **fields: str,
    ) -> bool:
        entry = dict(cache.get("ips", {}).get(ip, {}))
        updated = False
        for key, value in fields.items():
            if entry.get(key) != value:
                entry[key] = value
                updated = True
        if updated:
            cache.setdefault("ips", {})[ip] = entry
        return updated

    def _resolve_target(self, cache: LanCache, target: str) -> str | None:
        resolved = cache["aliases"].get(target.lower())
        if resolved and IPAddress(resolved):
            return resolved

        ip_addr = IPAddress(target)
        if ip_addr:
            return str(ip_addr)

        return None

    def _resolve_hostname(self, ip: IPAddress) -> str | None:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if hostname and hostname != ip:
                return hostname
        except Exception:
            hostname = None

        try:
            fqdn = socket.getfqdn(ip)
            if fqdn and fqdn != ip:
                return fqdn
        except Exception:
            return None

        return hostname

    def _lookup_mac_from_arp(self, ip: IPAddress | str) -> str | None:
        try:
            with open("/proc/net/arp", "r") as arp_file:
                lines = arp_file.readlines()[1:]
        except Exception:
            logger.exception("Error reading /proc/net/arp")
            return None

        for line in lines:
            parts = line.split()

            if len(parts) < 4:
                continue

            if parts[0] != ip:
                continue

            return parts[3].lower()

        return None

    def _lookup_vendor(self, mac: str) -> str | None:
        try:
            response = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
            if response.status_code == 200:
                vendor = response.text.strip()
                return vendor if vendor else None
        except Exception:
            logger.exception("Error looking up MAC vendor")
        return None

    def _latency_emoji(self, avg_rtt: float) -> str:
        if avg_rtt <= 50:
            return "🟢"
        elif avg_rtt <= 150:
            return "🟡"
        else:
            return "🔴"

    def _packet_loss_emoji(self, packet_loss: float) -> str:
        if packet_loss <= 0:
            return "🟢"
        elif packet_loss <= 5:
            return "🟡"
        else:
            return "🔴"

    def _request_hostname(
        self,
        cache: LanCache,
        ip: str,
    ) -> tuple[str | None, bool]:
        ip_addr = IPAddress(ip)
        if not ip_addr:
            return None, False

        entry = cache.get("ips", {}).get(ip, {})
        cached = entry.get("hostname") or None
        if cached and not self._is_stale(entry):
            return cached, False

        refreshed = self._resolve_hostname(ip_addr)
        if refreshed:
            updated = self._update_cache_entry(
                cache,
                ip,
                hostname=refreshed,
                updated_at=str(int(time.time())),
            )
            return refreshed, updated

        return cached, False

    def _request_mac(
        self,
        cache: LanCache,
        ip: str,
    ) -> tuple[str | None, bool]:
        ip_addr = IPAddress(ip)
        if not ip_addr:
            return None, False

        entry = cache.get("ips", {}).get(ip, {})
        cached = entry.get("mac") or None
        if cached and not self._is_stale(entry):
            return cached, False

        refreshed = self._lookup_mac_from_arp(ip_addr)
        if refreshed:
            updated = self._update_cache_entry(
                cache,
                ip,
                mac=refreshed,
                updated_at=str(int(time.time())),
            )
            return refreshed, updated

        return cached, False

    def _request_vendor(
        self,
        cache: LanCache,
        ip: str,
        mac: str | None,
    ) -> tuple[str | None, bool]:
        entry = cache.get("ips", {}).get(ip, {})
        cached = entry.get("vendor") or None
        if cached and not self._is_stale(entry):
            return cached, False

        if not mac:
            return cached, False

        refreshed = self._lookup_vendor(mac)
        if refreshed:
            updated = self._update_cache_entry(
                cache,
                ip,
                vendor=refreshed,
                updated_at=str(int(time.time())),
            )
            return refreshed, updated

        return cached, False

    @requires_admin()
    @commands.command(name="lan", description="Show statistics for a LAN device")
    async def lan(self, ctx: commands.Context, target: str, ping_count: int = 1):
        if ping_count < 1 or ping_count > 10:
            await send_error(ctx, description="Ping count must be between 1 and 10.")
            return

        cache = self._load_cache()
        resolved = self._resolve_target(cache, target)
        if not resolved:
            await send_error(ctx, description=f"Unknown target `{target}`. Use an IP or add an alias.")
            return

        ip_addr: IPAddress | None = IPAddress(resolved)
        if not ip_addr:
            await send_error(ctx, description=f"Error parsing IP address `{resolved}`. Ensure you provided a valid IPv4 address.")
            return

        cache_dirty = False
        host: icmplib.Host | None = self._ping_device(ip_addr, ping_count)
        ip_key = str(ip_addr)
        hostname, updated = self._request_hostname(cache, ip_key)
        cache_dirty = cache_dirty or updated

        mac, updated = self._request_mac(cache, ip_key)
        cache_dirty = cache_dirty or updated

        vendor, updated = self._request_vendor(cache, ip_key, mac)
        cache_dirty = cache_dirty or updated

        embed = discord.Embed(
            title="Device Stats",
            color=discord.Colour.blurple()
        )

        embed.add_field(name="🌐 IP Address", value=f"**`{ip_addr}`**")

        if target.lower() != ip_addr.lower():
            embed.add_field(name="🏷️ Alias", value=target)

        if hostname:
            embed.add_field(name="🖥️ Hostname", value=hostname)

        if host:
            if host.is_alive:
                embed.add_field(name="🛜 Status", value="Online", inline=False)
                embed.add_field(
                    name=f"{self._latency_emoji(host.avg_rtt)} Response Time",
                    value="\n".join([
                        f"- Min: **`{host.min_rtt}ms`**",
                        f"- Avg: **`{host.avg_rtt}ms`**",
                        f"- Max: **`{host.max_rtt}ms`**",
                    ]),
                    inline=False,
                )

                embed.add_field(name="📤 Packets Sent", value=f"**{host.packets_sent}**")
                embed.add_field(name="📥 Packets Received", value=f"**{host.packets_received}**")
                embed.add_field(name=f"{self._packet_loss_emoji(host.packet_loss)} Packet Loss", value=f"**{round(host.packet_loss)}%**")
            else:
                embed.add_field(name="❌ Status", value="Offline")

        if mac:
            embed.add_field(name="🔌 MAC Address", value=f"**`{mac}`**")
            embed.add_field(name="🏭 Vendor", value=vendor or "Unknown")

        if hostname or mac or vendor:
            cache_dirty = self._update_cache_entry(
                cache,
                ip_key,
                hostname=hostname or "",
                mac=mac or "",
                vendor=vendor or "",
                updated_at=cache.get("ips", {}).get(ip_key, {}).get("updated_at", ""),
            ) or cache_dirty

        if cache_dirty:
            self._save_cache(cache)

        await ctx.message.reply(embed=embed)

    @requires_admin()
    @commands.command(name="lan_refresh_cache", description="Remove cached LAN info for an IP")
    async def refresh_cache(self, ctx: commands.Context, ip: str) -> None:
        ip_addr: IPAddress | None = IPAddress(ip)
        if not ip_addr:
            await send_error(ctx, description=f"Error parsing IP address `{ip}`. Ensure you provided a valid IPv4 address.")
            return

        cache = self._load_cache()
        ip_key = str(ip_addr)
        existed = cache.get("ips", {}).pop(ip_key, None) is not None
        self._save_cache(cache)

        if existed:
            await send_success(ctx, description=f"Cleared cached info for `{ip_key}`.")
        else:
            await send_warning(ctx, title="No Cached Info", description=f"No cached info found for `{ip_key}`.")

    @requires_admin()
    @commands.command(name="lan_setalias", description="Set an alias for a LAN IP")
    async def lan_alias_set(self, ctx: commands.Context, alias: str, ip: str) -> None:
        ip_addr: IPAddress | None = IPAddress(ip)
        if not ip_addr:
            await send_error(ctx, description=f"Error parsing IP address `{ip}`. Ensure you provided a valid IPv4 address.")
            return

        cache = self._load_cache()
        alias_map = cache.get("aliases", {})
        if not isinstance(alias_map, dict):
            alias_map = {}

        normalized = alias.lower()
        alias_map[normalized] = str(ip_addr)
        cache["aliases"] = alias_map
        self._save_cache(cache)

        await send_success(ctx, description=f"Alias `{normalized}` set for `{ip_addr}`.")

    @requires_admin()
    @commands.command(name="lan_rmalias", description="Remove a LAN alias")
    async def lan_alias_remove(self, ctx: commands.Context, alias: str) -> None:
        cache = self._load_cache()
        alias_map = cache.get("aliases", {})

        if not isinstance(alias_map, dict):
            alias_map = {}

        normalized = alias.lower()
        existed = alias_map.pop(normalized, None) is not None
        cache["aliases"] = alias_map
        self._save_cache(cache)

        if existed:
            await send_success(ctx, description=f"Alias `{normalized}` has been successfully removed.")
        else:
            await send_error(ctx, description=f"Alias `{normalized}` not found.")

    @requires_admin()
    @commands.command(name="lan_lsalias", description="List LAN aliases")
    async def lan_alias_list(self, ctx: commands.Context) -> None:
        cache = self._load_cache()
        alias_map = cache.get("aliases", {})

        if not alias_map:
            await send_warning(ctx, title="No Aliases", description="No aliases found.")
            return

        await send_info(
            ctx,
            title="Aliases",
            description="\n".join([f"- `{alias}`: `{ip}`" for alias, ip in sorted(alias_map.items())])
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(LAN(bot))
