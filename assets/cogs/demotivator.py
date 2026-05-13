import asyncio
import pathlib
import random

import discord
from discord.ext import commands
from httpx import AsyncClient
from PIL import Image, ImageDraw, ImageFont

from modules.embeds import send_error
from modules.markovmemory import load_markov_model

generated_sentences = set()


def get_tnr(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        pathlib.Path(__file__).parent.parent / "fonts" / "timesnewroman.ttf",
        size,
    )


async def gen(
    input_image_path: pathlib.Path,
    max_attempts: int = 5,
) -> pathlib.Path | None:
    markov_model = load_markov_model()
    if not markov_model or not (await asyncio.to_thread(input_image_path.is_file)):
        return None

    attempt = 0
    while attempt < max_attempts:
        with Image.open(input_image_path).convert("RGB") as img:
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

            canvas.save(input_image_path)
            return input_image_path

        attempt += 1

    return None


class Demotivator(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "🖼️|Generates a demotivator poster"

    @commands.command()
    async def demotivator(self, ctx: commands.Context) -> None:
        if len(ctx.message.attachments) > 0:
            img_url = ctx.message.attachments[0].url

            if not img_url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                await send_error(
                    ctx,
                    description="Unsupported format. Please upload a JPG, PNG, GIF, or WEBP image.",
                )
                return

            data = pathlib.Path(__file__).parent.parent.parent / "data" / "demotivator"
            data.mkdir(parents=True, exist_ok=True)

            async with AsyncClient(timeout=10) as client:
                resp = await client.get(img_url)
                img_path = data / f"{ctx.message.id}.{img_url.split('.')[-1]}"
                img_path.write_bytes(resp.content)

            result = await gen(img_path)

            if result:
                await ctx.send(file=discord.File(result))
            else:
                await ctx.send("Failed to generate demotivator.")
        else:
            try:
                img = random.choice(  # noqa: S311
                    list((pathlib.Path(__file__).parent.parent / "images").glob("*.*")),
                )
                result = await gen(img)
                if result:
                    await ctx.send(file=discord.File(result))
                else:
                    await ctx.send("Failed to generate demotivator.")
            except Exception as e:
                await ctx.send(f"Error: {e!s}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Demotivator(bot))
