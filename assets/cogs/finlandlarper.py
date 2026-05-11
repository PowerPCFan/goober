import logging
import random
import re

import discord
from discord.ext import commands

from modules.settings import instance as settings_manager

logger = logging.getLogger("goober")


class FinlandLarper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.regex = re.compile(r"\b(Finland|Suomi|Finnish)\b", flags=re.IGNORECASE)

        self.settings = settings_manager.get_plugin_settings("finlandlarper", {"chance": 1})
        self.chance = self.settings["chance"]

        self.replies: list[str] = [
            "ELÄKÖÖN SUOMI!!!!!",
            "SUOMI ON PARAS MAA!!",
            "SUOMI VOITTAA AINA!!",
            "SUOMI ON PARAS PAIKKA!!",
            "finland mentioned",
            "suomesta mainittiin",
            "voi ei, mitä helvettiä?!",
            "VOI SAATANA!!!!!",
            "perkele",
            "Voi vittujen kevät!",
            "Jumalauta!",
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.content or "http" in message.content:
            # block bots, empty messages, and links
            return

        if self.regex.search(message.content):
            try:
                randint = random.randint(1, self.chance)  # noqa: S311
                logger.debug(
                    f"[FinlandLarper] Message matched regex, rolled {randint} (1 in {self.chance} chance)",  # noqa: E501
                )
                if randint == 1:
                    await message.reply(random.choice(self.replies))  # noqa: S311
            except Exception:  # noqa: S110
                pass

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FinlandLarper(bot))
