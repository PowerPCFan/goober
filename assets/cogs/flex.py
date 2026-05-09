import discord
from discord.ext import commands
import cpuinfo
import psutil
import socket
import platform
from typing import Mapping, NamedTuple
from psutil._ntuples import shwtemp
from enum import Enum


def add_empty(embed: discord.Embed) -> None:
    embed.add_field(name="\u200b", value="\u200b", inline=True)


def get_localip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


class SensorGroup(NamedTuple):
    label: 'Component'
    raw_name: str
    sensors: list[shwtemp]


class Component(Enum):
    CPU = "CPU"
    ACPI = "ACPI"
    GPU = "GPU"
    NVMe_SSD = "NVMe SSD"
    Wi_Fi = "Wi-Fi"
    UNKNOWN = "Unknown"


ALIASES: Mapping[str, 'Component'] = {
    "k10temp": Component.CPU,
    "coretemp": Component.CPU,
    "cpu_thermal": Component.CPU,
    "acpitz": Component.ACPI,
    "amdgpu": Component.GPU,
    "nvme": Component.NVMe_SSD,
    "mt7921_phy0": Component.Wi_Fi
}


def get_temps() -> list['SensorGroup']:
    temps = psutil.sensors_temperatures()

    return [SensorGroup(
        label=ALIASES.get(group_name, Component.UNKNOWN),
        raw_name=group_name,
        sensors=sensor_readings
    ) for group_name, sensor_readings in temps.items()] if temps else []


def get_cpu_temp(temps: list['SensorGroup']) -> shwtemp | None:
    for group in temps:
        if group.label == Component.CPU or (group.label == Component.UNKNOWN and "cpu" in group.raw_name.lower()):
            return max(group.sensors, key=lambda s: s.current)
    return None


def get_label(component: Component, raw: str) -> str:
    if isinstance(component, Component) and component != Component.UNKNOWN:
        return component.value
    else:
        return raw


class Flex(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "💪|Flex your machine!!"

    @commands.command()
    async def flex(self, ctx: commands.Context, show_all_sensors: str = ""):
        if show_all_sensors.lower() == "all":
            show_all_sensors_bool = True
        else:
            show_all_sensors_bool = False

        os = f"{platform.system() if platform.system() != 'Darwin' else 'macOS'} {platform.release() if platform.system() != 'Darwin' else platform.mac_ver()[0]}"

        cpu: dict = cpuinfo.get_cpu_info()
        cpu_name = cpu["brand_raw"]
        cores = psutil.cpu_count(logical=False)
        threads = int(cpu["count"])
        cpu_utilization = round(psutil.cpu_percent(), 2)

        mem = psutil.virtual_memory()
        total_memory = mem.total / (1024**3)
        used_memory = mem.used / (1024**3)

        swap = psutil.swap_memory()
        total_swap = swap.total / (1024**3)
        used_swap = swap.used / (1024**3)

        temps: list['SensorGroup'] = get_temps()
        cputemp: shwtemp | None = get_cpu_temp(temps)

        hostname = platform.node()

        local_ip: str = get_localip()

        py_version = platform.python_version()

        embed = discord.Embed(
            title="💪 Flex",
            description="Some useful information about the machine I'm running on.",
            color=discord.Color.yellow()
        )

        embed.add_field(name="CPU", value=f"{cpu_name} ({cores} cores {threads} threads)", inline=True)
        embed.add_field(name="CPU utilization", value=f"{cpu_utilization}%", inline=True)
        if cputemp:
            embed.add_field(name="CPU Temperature", value=f"{round(cputemp.current)}°C", inline=True)
        else:
            add_empty(embed)

        embed.add_field(name="Installed RAM", value=f"{round(mem.total / (1024**3), 2)} GB", inline=True)
        embed.add_field(name="Memory Usage", value=f"{round(used_memory)} GB / {round(total_memory, 2)} GB ({round((used_memory / total_memory) * 100)}%)", inline=True)
        embed.add_field(name="Swap Usage", value=f"{round(used_swap, 2)} GB / {round(total_swap, 2)} GB ({round((used_swap / total_swap) * 100)}%)", inline=True)

        embed.add_field(name="Hostname", value=f"`{hostname}`", inline=True)
        embed.add_field(name="Local IP", value=f"`{local_ip}`", inline=True)
        add_empty(embed)

        embed.add_field(name="OS", value=os, inline=True)
        embed.add_field(name="Python Version", value=f"`{py_version}`", inline=True)
        add_empty(embed)

        if not show_all_sensors_bool:
            embed.set_footer(text="Run ?!flex all to show all sensor readings")

        await ctx.send(embed=embed)

        if temps and show_all_sensors_bool:
            temps_embed = discord.Embed(
                title="System Temperatures",
                color=discord.Color.blue()
            )

            for sg in sorted(temps, key=lambda x: get_label(x.label, x.raw_name)):
                temps_embed.add_field(
                    name=f"{get_label(sg.label, sg.raw_name)}",
                    value="\n".join([
                        f"- {f'`{s.label}`: ' if s.label else ''}{round(s.current)}°C" for s in sg.sensors
                    ]),
                    inline=True
                )

            await ctx.send(embed=temps_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Flex(bot))
