import random
import re
import logging
import json
import time
import markovify
import discord
from discord.ext import commands
from modules.embeds import send_error, send_info
from modules.markovmemory import (
    load_markov_model,
    save_markov_model,
    train_markov_model,
)
from modules.permission import requires_admin
from modules.sentenceprocessing import (
    improve_sentence_coherence,
    is_positive,
    rephrase_for_coherence,
    send_message,
)
from modules.settings import instance as settings_manager

logger = logging.getLogger("goober")

settings = settings_manager.settings


class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.name = "Markov model"
        self.description = "🧠 | Commands for Goober's Markov model"
        self.model: markovify.NewlineText | None = load_markov_model()

    @requires_admin()
    @commands.command()
    async def retrain(self, ctx: commands.Context):
        message_ref: discord.Message | None = await send_message(
            ctx, embed=discord.Embed(
                title="Retraining Model",
                description="Retraining the Markov model, please wait...",
                color=discord.Color.orange()
            )
        )

        if message_ref is None:
            logger.error("Failed to send message!")
            return

        try:
            with open(settings.bot.active_memory, "r") as f:
                memory: list[str] = json.load(f)
        except FileNotFoundError:
            await send_error(ctx, description="Memory file not found!")
            return
        except json.JSONDecodeError:
            await send_error(ctx, description="Memory file is corrupt!")
            return

        data_size: int = len(memory)

        processing_message_ref: discord.Message | None = await send_message(
            ctx, embed=discord.Embed(
                title="Processing Data",
                description=f"Processing `{data_size}` data points...",
                color=discord.Color.orange()
            )
        )

        if processing_message_ref is None:
            logger.error("Couldnt find message processing message!")

        start_time: float = time.time()

        model = train_markov_model(memory)
        if not model:
            logger.error("Failed to train markov model")
            await send_error(ctx, description="Failed to retrain!")
            return False

        self.model = model
        save_markov_model(self.model)

        logger.debug(f"Completed retraining in {round(time.time() - start_time, 3)}s")

        await send_message(
            ctx,
            embed=discord.Embed(
                title="Model Retrained",
                description=f"Markov model retrained successfully using {data_size} data points!",
                color=discord.Color.green(),
            ),
            edit=True,
            edit_message_reference=processing_message_ref,
        )

    @commands.command()
    async def talk(self, ctx: commands.Context, sentence_size: int = 5) -> None:
        if not self.model:
            await send_info(ctx, title="Not Enough Data", description="I need to learn more from messages before I can talk.")
            return

        response: str = ""
        if sentence_size == 1:
            response = (
                self.model.make_short_sentence(max_chars=200, tries=700)
                or 'I have nothing to say right now!'
            )

        else:
            response = improve_sentence_coherence(
                self.model.make_sentence(tries=100, max_words=sentence_size)
                or 'I have nothing to say right now!'
            )

        cleaned_response: str = re.sub(r"[^\w\s]", "", response).lower()
        coherent_response: str = rephrase_for_coherence(cleaned_response)

        if random.random() < 0.9 and is_positive(coherent_response):
            gif_url: str = random.choice(settings.bot.misc.positive_gifs)

            coherent_response = f"{coherent_response}\n[gif]({gif_url})"

        await send_message(ctx, coherent_response)


async def setup(bot: commands.Bot):
    await bot.add_cog(Markov(bot))
