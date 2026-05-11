import os
import discord
from discord.ext import commands
from modules.embeds import send_error
from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
import httpx
import psutil
import logging
from modules.sync_connector import instance as synchub
from typing import Literal

settings = settings_manager.settings

logger = logging.getLogger("goober")


class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.name = "General"
        self.description = "🌐 | Commands for various stuff"

    @commands.hybrid_command(description="Get help with bot commands")
    async def help(self, ctx: commands.Context, layout: Literal["h", "v"] = "h") -> None:
        embed: discord.Embed = discord.Embed(
            title="Bot Help",
            description=f"List of commands grouped by category. Do `{settings.bot.prefix}help v` to use a vertical layout",
            color=discord.Colour(0x000000),
        )

        command_categories: dict[str, list[str]] = {}
        category_descriptions: dict[str, str] = {}

        for cog_name, cog in self.bot.cogs.items():
            display_name = getattr(cog, "name", cog_name)
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

    @commands.hybrid_command(description="Check the bot's latency")
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.defer()
        latency: int = round(self.bot.latency * 1000)

        embed: discord.Embed = discord.Embed(
            title="Pong!",
            description=f'{settings.bot.misc.ping_line}\n`Bot Latency: {latency}ms`',
            color=discord.Colour(0x000000),
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Learn more about the bot")
    async def about(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            title='About me',
            description="",
            color=discord.Colour(0x000000),
        )

        embed.add_field(
            name='Name',
            value=settings.name,
            inline=False,
        )

        embed.add_field(name="GitHub", value="https://github.com/PowerPCFan/goober")

        await send_message(ctx, embed=embed)

    @commands.hybrid_command(description="View bot statistics and settings")
    async def stats(self, ctx: commands.Context) -> None:
        memory_file: str = settings.bot.active_memory
        file_size: int = os.path.getsize(memory_file)

        with open(memory_file, "r") as file:
            line_count: int = sum(1 for _ in file)

        embed: discord.Embed = discord.Embed(
            title="Bot stats",
            description="Data about the the bot's memory.",
            color=discord.Colour(0x000000),
        )
        embed.add_field(
            name="File Stats",
            value=f"Size: {file_size} bytes\nLines: {line_count}",
            inline=False,
        )

        mem_used_by_process = psutil.Process().memory_info().rss / 1024 ** 2

        embed.add_field(name="Memory Usage", value=f"This bot is using {round(mem_used_by_process)} MB")

        embed.add_field(
            name="Sync hub",
            value=f"Connected: {synchub.connected} (URL: `{synchub.url}`)",
            inline=False,
        )

        embed.add_field(
            name="Settings Overview",
            value="\n".join(f"**{itm.split(": ")[0]}**: {itm.split(": ")[1]}" for itm in [
                f"Name: {settings.name}",
                f"Prefix: `{settings.bot.prefix}`",
                f"Owners: {", ".join([f"<@{uid}>" for uid in settings.bot.owner_ids])}",
                f"Ping line: `{settings.bot.misc.ping_line}`",
                f"Memory sharing enabled: {settings.bot.allow_show_mem_command}",
                f"User training enabled: {settings.bot.user_training}",
                f"Song: {settings.bot.misc.activity.content}"
            ]),
            inline=False
        )

        await send_message(ctx, embed=embed)

    @requires_admin()
    @commands.hybrid_command(description="Share the bot's memory file")
    async def mem(self, ctx: commands.Context) -> None:
        if not settings.bot.allow_show_mem_command:
            return

        with open(settings.bot.active_memory, "rb") as f:
            data: bytes = f.read()

        if len(data) > (10 * 1024 * 1024):
            async with httpx.AsyncClient() as c:
                response = await c.post(
                    "https://litterbox.catbox.moe/resources/internals/api.php",
                    data={"reqtype": "fileupload", "time": "1h"},
                    files={"fileToUpload": data},
                )

            if response.status_code != 200:
                await send_error(ctx, description="Failed to upload memory file to catbox.moe. Try again later.")
        else:
            await ctx.send(file=discord.File(data))
            return


async def setup(bot: commands.Bot):
    print("Setting up base_commands")
    await bot.add_cog(BaseCommands(bot))
