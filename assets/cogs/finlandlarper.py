import logging
import random
import re
from typing import TypedDict

import discord
from discord.ext import commands

from modules.settings import instance as settings_manager

logger = logging.getLogger("goober")


class FinlandLarperSettings(TypedDict):
    chance: int


class FinlandLarper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.regex = re.compile(r"\b(Finland|Suomi|Finnish)\b", flags=re.IGNORECASE)
        self.settings: FinlandLarperSettings = settings_manager.get_plugin_settings(
            "finlandlarper", {"chance": 1}
        )  # type: ignore
        self.chance = self.settings["chance"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or "http" in message.content:
            # block bots, empty messages, and links
            return

        if self.regex.search(message.content):
            try:
                randint = random.randint(1, self.chance)
                logger.debug(
                    f"[FinlandLarper] Message matched regex, rolled {randint} (1 in {self.chance} chance)"  # noqa: E501
                )
                if randint == 1:
                    await message.reply("ELÄKÖÖN SUOMI!!!!!!")
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(FinlandLarper(bot))
