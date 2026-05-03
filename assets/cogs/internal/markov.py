import os
import random
import re
import discord
from discord.ext import commands

import discord.ext
import discord.ext.commands

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
import modules.keys as k
import logging
from typing import List, Optional, Set
import json
import time
import markovify


logger = logging.getLogger("goober")
from modules.settings import instance as settings_manager

settings = settings_manager.settings


class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.ext.commands.Bot = bot

        self.model: markovify.NewlineText | None = load_markov_model()

    @requires_admin()
    @commands.command()
    async def retrain(self, ctx: discord.ext.commands.Context):
        message_ref: discord.Message | None = await send_message(
            ctx, f"{'Retraining the Markov model... Please wait.'}"
        )

        if message_ref is None:
            logger.error("Failed to send message!")
            return

        try:
            with open(settings.bot.active_memory, "r") as f:
                memory: List[str] = json.load(f)
        except FileNotFoundError:
            await send_message(ctx, f"{'Error: memory file not found!'}")
            return
        except json.JSONDecodeError:
            await send_message(ctx, f"{'Error: memory file is corrupt!'}")
            return

        data_size: int = len(memory)

        processing_message_ref: discord.Message | None = await send_message(
            ctx, f"Processing {data_size} data points..."
        )
        if processing_message_ref is None:
            logger.error("Couldnt find message processing message!")

        start_time: float = time.time()

        model = train_markov_model(memory)
        if not model:
            logger.error("Failed to train markov model")
            await ctx.send("Failed to retrain!")
            return False

        self.model = model
        save_markov_model(self.model)

        logger.debug(f"Completed retraining in {round(time.time() - start_time,3)}s")

        await send_message(
            ctx,
            f"Markov model retrained successfully using {data_size} data points!",
            edit=True,
            message_reference=processing_message_ref,
        )

    @commands.command()
    async def talk(self, ctx: commands.Context, sentence_size: int = 5) -> None:
        if not self.model:
            await send_message(ctx, f"{'I need to learn more from messages before I can talk.'}")
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

            coherent_response = f"{coherent_response}\n[jif]({gif_url})"

        os.environ["gooberlatestgen"] = coherent_response
        await send_message(ctx, coherent_response)


async def setup(bot):
    await bot.add_cog(Markov(bot))
