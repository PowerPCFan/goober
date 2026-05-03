import discord
from discord.ext import commands
import markovify
from PIL import Image, ImageDraw, ImageFont
import os
from modules.markovmemory import load_markov_model
from textwrap import wrap
import logging
from modules.settings import instance as settings_manager
import re
import time

logger = logging.getLogger("goober")

settings = settings_manager.settings


class BreakingNews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.font_size = 90
        self.image_margin = -25
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(
            os.path.join("assets", "fonts", "SpecialGothic.ttf"), self.font_size
        )
        self.description = "🚨|Lets you make your very own news stories"

        self.model: markovify.NewlineText | None = load_markov_model()

    @commands.command()
    async def auto_create(self, ctx: commands.Context, enabled: str | None):
        if enabled not in ["yes", "no"]:
            await ctx.send(
                f'Please use {settings["bot"]["prefix"]}auto_create <yes | no>'
            )
            return False

        mode: bool = enabled == "yes"

        settings_manager.set_plugin_setting(
            "breaking_news", {"create_from_message_content": mode}
        )

        await ctx.send("Changed setting!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not settings_manager.get_plugin_settings(
            "breaking_news", {"create_from_message_content": False}
        ).get("create_from_message_content"):
            logger.debug("Ignoring message - create_from_message_content not enabled")
            return

        if not message.content.lower().startswith("breaking news:"):
            return

        texts: list[str] = re.split("breaking news:", message.content, flags=re.IGNORECASE)

        logger.debug(texts)
        try:
            text: str | None = texts[1].strip()

            if not text or self.model is None:
                await message.reply("No news specified and model not found!")
                return False

            text = text or self.model.make_sentence(max_chars=50, tries=50)
            path = self.__insert_text(text or "")
        except IndexError:
            if self.model is None:
                await message.reply("No model loaded and no breaking news specified")
                return False

            path = self.__insert_text(
                self.model.make_sentence(max_chars=50, tries=50) or ""
            )
            await message.reply("You didn't specify any breaking news!")

        with open(path, "rb") as f:
            await message.reply(file=discord.File(f))

    @commands.command()
    async def breaking_news(self, ctx: commands.Context, *args):
        if not self.model:
            await ctx.send("Please supply a message!")
            return False

        message = " ".join(args) or self.model.make_sentence(max_chars=50, tries=50)

        if not message:
            await ctx.send("Please supply a message!")
            return False

        with open(self.__insert_text(message), "rb") as f:
            await ctx.send(content="Breaking news!", file=discord.File(f))

    def __insert_text(self, text: str):
        start = time.time()
        base_image_data: Image.ImageFile.ImageFile = Image.open(
            os.path.join("assets", "images", "breaking_news.png")
        )

        base_image: ImageDraw.ImageDraw = ImageDraw.Draw(base_image_data)

        MAX_IMAGE_WIDTH = base_image_data.width - self.image_margin

        if len(text) * self.font_size > MAX_IMAGE_WIDTH:
            parts = wrap(text, MAX_IMAGE_WIDTH // self.font_size)
            logger.debug(parts)
            for index, part in enumerate(parts):
                text_size = base_image.textlength(part, self.font)

                base_image.text(
                    (
                        self.image_margin / 2 + ((MAX_IMAGE_WIDTH - text_size) / 2),
                        (base_image_data.height * 0.2) + index * self.font_size,
                    ),
                    part,
                    font=self.font,
                )
        else:
            text_size = base_image.textlength(text, self.font)

            base_image.text(
                (
                    self.image_margin / 2 + ((MAX_IMAGE_WIDTH - text_size) / 2),
                    (base_image_data.height * 0.2),
                ),
                text,
                font=self.font,
            )

        path_folders = os.path.join("assets", "images", "cache")
        os.makedirs(path_folders, exist_ok=True)

        path = os.path.join(path_folders, "breaking_news.png")

        with open(path, "wb") as f:
            base_image_data.save(f)

        logger.info(f"Generation took {time.time() - start}s")

        return path


async def setup(bot: commands.Bot):
    await bot.add_cog(BreakingNews(bot))
