import discord
import discord.context_managers
from discord.ext import commands
import logging
from typing import Literal, get_args, cast
from modules.permission import requires_admin
from modules.settings import instance as settings_manager

settings = settings_manager.settings


logger = logging.getLogger("goober")

AvailableModes = Literal["r", "s"]


class FileSync(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.mode: AvailableModes | None = None
        self.peer_id = None
        self.awaiting_file = False
        self.description = "🛜|Send and receive files between bots"


    @requires_admin()
    @commands.command()
    async def syncfile(self, ctx: commands.Context, mode: str, peer: discord.User):
        if self.mode not in get_args(AvailableModes):
            await ctx.send("Invalid mode, use 's' or 'r'.")
            return

        self.mode = cast(AvailableModes, mode.lower())
        self.peer_id = peer.id

        if self.mode == "s":
            await ctx.send(f"<@{self.peer_id}> FILE_TRANSFER_REQUEST")
            await ctx.send(file=discord.File(settings.bot.active_memory))
            await ctx.send("File sent in this channel.")

        elif self.mode == "r":
            await ctx.send("Waiting for incoming file...")
            self.awaiting_file = True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or not self.awaiting_file:
            return

        if message.author.id != self.peer_id:
            return

        if message.content == "FILE_TRANSFER_REQUEST":
            logger.info("Ping received. Awaiting file...")
        if not message.attachments:
            return

        for attachment in message.attachments:
            if not attachment.filename.endswith(".json"):
                continue

            filename = "received_memory.json"
            with open(filename, "wb") as f:
                await attachment.save(f)

            logger.info(f"File saved as {filename}")
            await message.channel.send("File received and saved.")
            self.awaiting_file = False


async def setup(bot):
    await bot.add_cog(FileSync(bot))
