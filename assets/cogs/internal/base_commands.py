import os
import discord
from discord.ext import commands
from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
import requests
import psutil
import cpuinfo
import sys
import platform
import logging
from modules.sync_connector import instance as synchub

settings = settings_manager.settings

OS_STRING = f"{platform.system() if platform.system() != 'Darwin' else 'macOS'} {platform.release() if platform.system() != 'Darwin' else platform.mac_ver()[0]}"

logger = logging.getLogger("goober")


class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "🌐 | General commands for various stuff"

    @commands.command()
    async def help(self, ctx: commands.Context, layout: str = "h") -> None:
        embed: discord.Embed = discord.Embed(
            title="Bot Help",
            description=f"List of commands grouped by category. Do `{settings.bot.prefix}help v` to use a vertical layout",
            color=discord.Colour(0x000000),
        )

        category_aliases: dict[str, str] = {
            "BaseCommands": "General",
            "SyncHubManagement": "Sync Hub",
            "CogManager": "Cog Management",
            "PermissionManager": "Permission Management",
            "Markov": "Markov model",
            "SongChanger": "Song Changer",
            "WhoAmI": "Who Am I?"
        }

        command_categories: dict[str, list[str]] = {}
        category_descriptions: dict[str, str] = {}

        for cog_name, cog in self.bot.cogs.items():
            display_name = category_aliases.get(cog_name, cog_name)
            commands_list = command_categories.setdefault(display_name, [])
            category_descriptions.setdefault(display_name, getattr(cog, "description", "No description"))

            for command in cog.get_commands():
                if command.hidden:
                    continue
                commands_list.append(command.name)

        for category, commands_list in command_categories.items():
            if not commands_list:
                continue

            commands_in_category: str = "\n".join([f"{settings.bot.prefix}**{command}**" for command in commands_list])
            description = category_descriptions.get(category, 'No description')
            emoji = ""

            if "|" in description:
                emoji, description = description.split("|", 1)

            emoji = emoji.strip() + " "  # normalize spacing

            embed_value = f"{description}\n\n{commands_in_category}\n‌"  # don't remove zero width non joiner since it adds spacing
            embed.add_field(name=f"{emoji} {category}", value=embed_value, inline=(False if layout == "v" else True))

        await send_message(ctx, embed=embed)

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.defer()
        latency: int = round(self.bot.latency * 1000)

        embed: discord.Embed = discord.Embed(
            title="Pong!",
            description=f'{settings.bot.misc.ping_line}\n`Bot Latency: {latency}ms`',
            color=discord.Colour(0x000000),
        )
        embed.set_footer(
            text=f"{'Requested by'} {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            title='About me',
            description="",
            color=discord.Colour(0x000000),
        )

        embed.add_field(
            name='System information',
            value=f'OS: {OS_STRING}'
        )

        embed.add_field(
            name='Name',
            value=settings.name,
            inline=False,
        )

        embed.add_field(name="GitHub", value="https://github.com/PowerPCFan/goober")

        await send_message(ctx, embed=embed)

    @commands.command()
    async def stats(self, ctx: commands.Context) -> None:
        memory_file: str = settings.bot.active_memory
        file_size: int = os.path.getsize(memory_file)

        memory_info = psutil.virtual_memory()
        total_memory = memory_info.total / (1024**3)
        used_memory = memory_info.used / (1024**3)

        cpu_name = cpuinfo.get_cpu_info()["brand_raw"]

        with open(memory_file, "r") as file:
            line_count: int = sum(1 for _ in file)

        embed: discord.Embed = discord.Embed(
            title=f"{'Bot stats'}",
            description="Data about the the bot's memory.",
            color=discord.Colour(0x000000),
        )
        embed.add_field(
            name=f"{'File Stats'}",
            value=f"{'Size: {file_size} bytes\nLines: {line_count}'.format(file_size=file_size, line_count=line_count)}",
            inline=False,
        )

        mem_used_by_process = psutil.Process().memory_info().rss / 1024 ** 2

        embed.add_field(name="Instance", value=f"Memory usage: {round(mem_used_by_process)}mb")

        embed.add_field(
            name='System information',
            value="\n".join([
                f"Memory Usage: {round(used_memory)} GB / {round(total_memory, 2)} GB ({round((used_memory / total_memory) * 100)}%)",
                f"CPU: {cpu_name}"
            ])
        )

        embed.add_field(
            name="Sync hub",
            value=f"Connected: {synchub.connected}, URL: {synchub.url}",
            inline=False,
        )

        embed.add_field(
            name="Variable Info",
            value=f"""{"Name: {NAME} \nPrefix: {PREFIX} \nOwner ID: {ownerid}\nPing line: {PING_LINE} \nMemory Sharing Enabled: {showmemenabled} \nUser Training Enabled: {USERTRAIN_ENABLED}\nSong: {song}".format(  # noqa: E501 somehow this is longer than 200 chars
                NAME=settings.name, PREFIX=settings.bot.prefix, ownerid=settings.bot.owner_ids[0],
                PING_LINE=settings.bot.misc.ping_line, showmemenabled=settings.bot.allow_show_mem_command,
                USERTRAIN_ENABLED=settings.bot.user_training, song=settings.bot.misc.activity.content
            )}""",
            inline=False,
        )

        await send_message(ctx, embed=embed)

    @requires_admin()
    @commands.command()
    async def restart(self, ctx: commands.Context):
        await ctx.send("Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @requires_admin()
    @commands.command()
    async def force_update(self, ctx: commands.Context):
        await ctx.send("Forcefully updating...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @requires_admin()
    @commands.command()
    async def mem(self, ctx: commands.Context) -> None:
        if not settings.bot.allow_show_mem_command:
            return

        with open(settings.bot.active_memory, "rb") as f:
            data: bytes = f.read()

        response = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "1h"},
            files={"fileToUpload": data},
        )

        if response.status_code != 200:
            with open(settings.bot.active_memory, "rb") as f:
                await send_message(ctx, file=discord.File(f))
                return

        await send_message(ctx, response.text)


async def setup(bot: commands.Bot):
    print("Setting up base_commands")
    await bot.add_cog(BaseCommands(bot))
