import io
import logging
import pathlib
import random

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from modules.embeds import send_error
from modules.markovmemory import load_markov_model

logger = logging.getLogger("goober")

generated_sentences = set()


def get_tnr(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        pathlib.Path(__file__).parent.parent / "fonts" / "timesnewroman.ttf",
        size,
    )


async def gen(  # noqa: C901, PLR0915
    image_path: pathlib.Path | io.BytesIO,
    max_attempts: int = 5,
) -> io.BytesIO | None:
    if not image_path:
        return None

    if isinstance(image_path, pathlib.Path) and not (image_path.exists() or image_path.is_file()):  # noqa: ASYNC240
        return None

    markov_model = load_markov_model()
    if not markov_model:
        return None

    attempt = 0
    while attempt < max_attempts:
        with Image.open(image_path).convert("RGB") as img:
            size = max(img.width, img.height)
            frame_thick = int(size * 0.0054)
            inner_size = size - 2 * frame_thick
            resized_img = img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
            framed = Image.new("RGB", (size, size), "white")
            framed.paste(resized_img, (frame_thick, frame_thick))
            landscape_w = int(size * 1.5)
            caption_h = int(size * 0.3)
            canvas_h = framed.height + caption_h
            canvas = Image.new("RGB", (landscape_w, canvas_h), "black")
            fx = (landscape_w - framed.width) // 2
            canvas.paste(framed, (fx, 0))

            draw = ImageDraw.Draw(canvas)

            title = subtitle = None
            for _ in range(20):
                t = markov_model.make_sentence(tries=100, max_words=4)
                s = markov_model.make_sentence(tries=100, max_words=5)
                if t and s and t != s:
                    title = t.upper()
                    subtitle = s.capitalize()
                    break
            if not title:
                title = "DEMOTIVATOR"
            if not subtitle:
                subtitle = "no text generated"

            title_sz = int(caption_h * 0.4)
            sub_sz = int(caption_h * 0.25)
            title_font = get_tnr(title_sz)
            sub_font = get_tnr(sub_sz)

            bbox = draw.textbbox((0, 0), title, font=title_font)
            txw, txh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (landscape_w - txw) // 2
            ty = framed.height + int(caption_h * 0.1)

            for ox, oy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text((tx + ox, ty + oy), title, font=title_font, fill="black")
            draw.text((tx, ty), title, font=title_font, fill="white")

            bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
            sxw, _ = bbox[2] - bbox[0], bbox[3] - bbox[1]
            sx = (landscape_w - sxw) // 2
            sy = ty + txh + int(caption_h * 0.05)
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                draw.text((sx + ox, sy + oy), subtitle, font=sub_font, fill="black")
            draw.text((sx, sy), subtitle, font=sub_font, fill="#AAAAAA")

            demotivator = io.BytesIO()
            canvas.save(demotivator, format="PNG")
            demotivator.seek(0)
            return demotivator

        attempt += 1

    return None


class Demotivator(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "🖼️|Generates a demotivator poster"

        self.allowed_ext = (".jpg", ".jpeg", ".png", ".gif", ".webp")

    async def _validate_and_process_image(
        self, image: discord.Attachment,
    ) -> io.BytesIO | None:
        image_type = image.content_type or ""
        image_name = image.filename.lower()

        if not image_type.startswith("image/") or not image_name.endswith(self.allowed_ext):
            return None

        try:
            img_bytes = await image.read()
            img_bytesio = io.BytesIO(img_bytes)

            with Image.open(img_bytesio) as test_img:
                test_img.load()

            img_bytesio.seek(0)
        except (UnidentifiedImageError, OSError):
            return None
        else:
            return img_bytesio

    async def _generate_and_send(
        self,
        ctx_or_interaction: commands.Context | discord.Interaction,
        image_source: pathlib.Path | io.BytesIO | None = None,
    ) -> None:
        try:
            if image_source is None:
                image_source = random.choice(  # noqa: S311
                    list((pathlib.Path(__file__).parent.parent / "images").glob("*.*")),
                )

            result = await gen(image_source)

            if result:
                file = discord.File(result, filename="demotivator.png")
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.send(file=file)
                else:
                    await ctx_or_interaction.response.send_message(file=file)
            else:
                await send_error(ctx_or_interaction, description="Failed to generate demotivator.")
        except Exception:
            logger.exception("Error generating demotivator")
            await send_error(ctx_or_interaction, description="Failed to generate demotivator.")

    @commands.command()
    async def demotivator(self, ctx: commands.Context) -> None:
        if len(ctx.message.attachments) > 0:
            image_bytesio = await self._validate_and_process_image(ctx.message.attachments[0])
            if image_bytesio is None:
                await send_error(
                    ctx,
                    description=(
                        "Unsupported format or corrupted image. "
                        "Please upload a valid JPG, PNG, GIF, or WEBP."
                    ),
                )
                return
            await self._generate_and_send(ctx, image_bytesio)
        else:
            await self._generate_and_send(ctx)

    @app_commands.command(name="demotivator", description="Generate a demotivator poster")
    @app_commands.describe(
        image="(optional) Image file to use for the demotivator. Falls back to random image",
    )
    async def demotivator_slash(
        self,
        interaction: discord.Interaction,
        image: discord.Attachment | None = None,
    ) -> None:
        if image:
            image_bytesio = await self._validate_and_process_image(image)
            if image_bytesio is None:
                await send_error(
                    interaction,
                    description=(
                        "Unsupported format or corrupted image. "
                        "Please upload a valid JPG, PNG, GIF, or WEBP."
                    ),
                )
                return
            await self._generate_and_send(interaction, image_bytesio)
        else:
            await self._generate_and_send(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Demotivator(bot))
