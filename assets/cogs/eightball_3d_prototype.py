import pathlib
import random
from discord.ext import commands
import discord
import asyncio
from PIL import Image, ImageDraw, ImageFont


class Eightball(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "🎱|It is certainly an 8-ball"

        self.data = pathlib.Path(__file__).parent.parent.parent / "data" / "eightball"
        self.data.mkdir(exist_ok=True)

        self.tnr = pathlib.Path(__file__).parent.parent / "fonts" / "timesnewroman.ttf"

        self.responses = [
            # positive
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",

            # unsure
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",

            # negative
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]

    @commands.command()
    async def eightball(self, ctx: commands.Context, *, question: str = ""):
        # Send initial message
        msg1_embed = discord.Embed(
            title="🎱 The Magic 8-Ball says:",
            description="Rolling...",
            color=discord.Color.greyple(),
        )
        msg1 = await ctx.send(embed=msg1_embed)

        choice = random.choice(self.responses)
        output_path = self.data / f"8ball-{ctx.message.id}.gif"
        renderer = EightballRenderer(font_path=self.tnr)
        renderer.generate_eightball_gif(choice, output_path, question, ctx.author.name)

        # Send GIF
        await ctx.send(file=discord.File(output_path))

        # Now that GIF is sent, wait for the GIF to play a little before editing
        # await asyncio.sleep(3)
        await asyncio.sleep(0.25)

        # Edit
        msg1_embed.description = f"{choice}"
        msg1 = await msg1.edit(embed=msg1_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Eightball(bot))


class EightballRenderer:
    def __init__(
        self,
        *,
        size: int = 600,
        ball_radius: int = 220,
        badge_radius: int = 90,
        triangle_width: int = 228,
        triangle_height: int = 190,
        font_path: pathlib.Path,
    ) -> None:
        self.size = size
        self.scale = max(1.0, size / 300)
        self.center = size // 2
        self.ball_radius = ball_radius
        self.badge_radius = badge_radius
        self.triangle_width = triangle_width
        self.triangle_height = triangle_height
        self.font_path = font_path

    def render_ball_base(
        self,
        show_badge: bool,
        light_phase: float = -0.5,
        badge_offset: tuple[int, int] = (0, 0),
        badge_alpha: int = 255,
        badge_scale: tuple[float, float] = (1.0, 1.0),
        badge_clip: float = 0.0,
    ) -> Image.Image:
        img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse(
            (
                self.center - self.ball_radius,
                self.center - self.ball_radius,
                self.center + self.ball_radius,
                self.center + self.ball_radius,
            ),
            fill=(8, 8, 8, 255),
        )
        draw.ellipse(
            (
                self.center - self.ball_radius,
                self.center - self.ball_radius,
                self.center + self.ball_radius,
                self.center + self.ball_radius,
            ),
            outline=(0, 0, 0, 220),
            width=max(1, int(2 * self.scale)),
        )
        if show_badge:
            badge = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)
            badge_w = self.badge_radius * badge_scale[0]
            badge_h = self.badge_radius * badge_scale[1]
            badge_box = (
                self.center - badge_w + badge_offset[0],
                self.center - badge_h + badge_offset[1],
                self.center + badge_w + badge_offset[0],
                self.center + badge_h + badge_offset[1],
            )
            bdraw.ellipse(badge_box, fill=(255, 255, 255, badge_alpha))
            badge_font = ImageFont.truetype(str(self.font_path), int(52 * self.scale))
            bbox = bdraw.textbbox((0, 0), "8", font=badge_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            text_x = self.center - text_w / 2 + badge_offset[0]
            text_y = self.center - text_h / 2 - int(10 * self.scale) + badge_offset[1]
            for dx, dy in [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, 1)]:
                bdraw.text(
                    (text_x + dx, text_y + dy),
                    "8",
                    fill=(0, 0, 0, badge_alpha),
                    font=badge_font,
                )
            if badge_clip > 0:
                mask = Image.new("L", (self.size, self.size), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.ellipse(
                    (
                        self.center - self.ball_radius,
                        self.center - self.ball_radius,
                        self.center + self.ball_radius,
                        self.center + self.ball_radius,
                    ),
                    fill=int(255 * (1.0 - badge_clip)),
                )
                badge.putalpha(Image.composite(badge.split()[-1], mask, mask))
            img.alpha_composite(badge)
        return img

    def render_answer_overlay(self, text: str, opacity: int) -> Image.Image | None:
        overlay = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        triangle_offset = -12 * self.scale
        triangle = [
            (self.center, self.center - self.triangle_height / 2 + triangle_offset),
            (self.center - self.triangle_width / 2, self.center + self.triangle_height / 2 + triangle_offset),
            (self.center + self.triangle_width / 2, self.center + self.triangle_height / 2 + triangle_offset),
        ]
        draw.polygon(triangle, fill=(70, 120, 200, opacity))
        draw.line(triangle + [triangle[0]], fill=(40, 80, 150, opacity), width=2)

        top_y = self.center - self.triangle_height / 2 + triangle_offset
        bottom_y = self.center + self.triangle_height / 2 + triangle_offset
        text_top = top_y + self.triangle_height * 0.26
        bottom_limit = bottom_y - self.triangle_height * 0.08
        text_bounds_h = max(10.0, bottom_limit - text_top)

        def max_width_at(y: float) -> float:
            progress = (y - top_y) / self.triangle_height
            progress = max(0.1, min(1.0, progress))
            return self.triangle_width * progress * 0.95

        def wrap_for_triangle(font: ImageFont.FreeTypeFont, line_height: float) -> list[str]:
            words = text.split()
            lines: list[str] = []
            line = ""
            for word in words:
                test = word if not line else f"{line} {word}"
                lines.append(test)
                line_y = text_top + (len(lines) - 0.5) * line_height
                max_width = max_width_at(line_y)
                lines.pop()
                test_width = draw.textlength(test, font=font)
                if test_width <= max_width:
                    line = test
                    continue
                if line:
                    lines.append(line)
                    line = word
                else:
                    lines.append(word)
                    line = ""
            if line:
                lines.append(line)
            return lines

        font: ImageFont.FreeTypeFont | None = None
        lines: list[str] = []

        font_size = int(18 * self.scale)
        min_font = max(8, int(11 * self.scale))
        while font_size >= min_font:
            font = ImageFont.truetype(str(self.font_path), font_size)
            line_height = font.size * 1.1
            lines = wrap_for_triangle(font, line_height)
            block_height = line_height * len(lines)
            if block_height <= text_bounds_h:
                widest = 0.0
                for i, line in enumerate(lines):
                    line_y = text_top + (i + 0.5) * line_height
                    widest = max(widest, draw.textlength(line, font=font) - max_width_at(line_y))
                if widest <= 0:
                    break
            font_size -= 1

        if not font or not lines:
            return None

        line_height = font.size * 1.1
        spacing = line_height - font.size
        joined = "\n".join(lines)
        bbox = draw.multiline_textbbox((0, 0), joined, font=font, align="center", spacing=spacing)
        width = bbox[2] - bbox[0]
        text_x = self.center - width / 2
        text_y = text_top + (text_bounds_h - (bbox[3] - bbox[1])) / 2
        draw.multiline_text(
            (text_x, text_y),
            joined,
            fill=(235, 245, 255, opacity),
            font=font,
            align="center",
            spacing=spacing,
        )
        return overlay

    def _footer_text(self, question: str, username: str) -> str:
        if question and question.strip():
            return f"@{username} asked: {question.strip()}"
        return f"Generated by @{username}"

    def _truncate_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
        if draw.textlength(text, font=font) <= max_width:
            return text
        trimmed = text
        while len(trimmed) > 3 and draw.textlength(trimmed + "...", font=font) > max_width:
            trimmed = trimmed[:-1]
        if len(trimmed) <= 3:
            return "..."
        return trimmed + "..."

    def _draw_footer_text(self, image: Image.Image, text: str) -> None:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(str(self.font_path), int(11 * self.scale))
        max_width = self.size * 0.9
        safe_text = self._truncate_text(draw, text, font, max_width)
        bbox = draw.textbbox((0, 0), safe_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.size - text_width) / 2
        text_y = self.size - text_height - int(10 * self.scale)
        pad_x = int(4 * self.scale)
        pad_y = int(2 * self.scale)
        draw.rectangle(
            (text_x - pad_x, text_y - pad_y, text_x + text_width + pad_x, text_y + text_height + pad_y),
            fill=(0, 0, 0, 200),
        )
        draw.text((text_x, text_y), safe_text, fill=(245, 245, 245, 230), font=font)

    def _badge_motion(self, progress: float) -> tuple[tuple[int, int], tuple[float, float], int, float]:
        progress = max(0.0, min(1.0, progress))
        badge_offset_y = int(-self.badge_radius * (2.2 * progress))
        badge_distortion = max(0.0, min(1.0, abs(badge_offset_y) / (self.badge_radius * 2.4)))
        badge_offset = (0, badge_offset_y)
        badge_scale = (
            1.0 + 0.18 * badge_distortion,
            max(0.1, 1.0 - 0.9 * badge_distortion),
        )
        badge_alpha = int(255 * (1.0 - badge_distortion))
        badge_clip = max(0.0, min(1.0, (badge_distortion - 0.55) / 0.45))
        return badge_offset, badge_scale, badge_alpha, badge_clip

    def generate_eightball_gif(self, choice: str, output_path: pathlib.Path, question: str, username: str) -> None:
        frames: list[Image.Image] = []
        base_badge = self.render_ball_base(True, light_phase=-0.6)
        base_answer = self.render_ball_base(False, light_phase=0.6)
        footer_text = self._footer_text(question, username)

        for _ in range(10):
            frame = base_badge.copy()
            self._draw_footer_text(frame, footer_text)
            frames.append(frame)

        base_offsets = [
            -2, 2, -3, 3, -4, 4, -5, 5,
            -4, 4, -3, 3, -2, 2, -1, 1, 0,
        ]
        shake_offsets = [int(offset * self.scale) for offset in base_offsets]
        for offset in shake_offsets:
            base = self.render_ball_base(True)
            frame = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
            frame.paste(base, (offset, 0))
            self._draw_footer_text(frame, footer_text)
            frames.append(frame)

        flip_frames = 20
        switch_at = 0.5
        for i in range(flip_frames):
            t = i / (flip_frames - 1)
            light_phase = (t * 2 - 1) * 0.9
            badge_progress = max(0.0, min(1.0, (t / switch_at)))
            badge_offset, badge_scale, badge_alpha, badge_clip = self._badge_motion(badge_progress)
            base = self.render_ball_base(
                t < switch_at,
                light_phase=light_phase,
                badge_offset=badge_offset,
                badge_alpha=badge_alpha,
                badge_scale=badge_scale,
                badge_clip=badge_clip,
            )
            frame = base.copy()
            self._draw_footer_text(frame, footer_text)
            frames.append(frame)

        for opacity in range(0, 256, 8):
            frame = base_answer.copy()
            answer_overlay = self.render_answer_overlay(choice, opacity)
            if not answer_overlay:
                raise Exception("Failed to render answer overlay")
            frame.alpha_composite(answer_overlay)
            self._draw_footer_text(frame, footer_text)
            frames.append(frame)

        for _ in range(40):
            frames.append(frames[-1].copy())

        frames[0].save(
            fp=output_path, save_all=True,
            append_images=frames[1:],
            duration=80, loop=0, disposal=2
        )
