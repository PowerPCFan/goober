import json
import logging
import pickle
from pathlib import Path

import markovify

from modules.settings import instance as settings_manager

settings = settings_manager.settings

model: markovify.NewlineText | None = None

logger = logging.getLogger("goober")

active_mem = Path(settings.bot.active_memory)
active_model = Path(settings.bot.active_model)


def load_memory() -> list:
    data = []

    try:
        with active_mem.open() as f:
            data = json.load(f)
    except FileNotFoundError:
        with active_mem.open("w") as f:
            json.dump([], f)
            data = []

    return data


def save_memory(memory: list) -> None:
    with active_mem.open("w") as f:
        json.dump(memory, f, indent=4)


def train_markov_model(
    memory: list,
    additional_data: list | None = None,
) -> markovify.NewlineText | None:
    if not memory:
        return None

    filtered_memory = [line for line in memory if isinstance(line, str)]
    if additional_data:
        filtered_memory.extend(line for line in additional_data if isinstance(line, str))

    if not filtered_memory:
        return None

    text = "\n".join(filtered_memory)
    return markovify.NewlineText(text, state_size=2)


def save_markov_model(model: markovify.NewlineText | None) -> None:
    with active_model.open("wb") as f:
        pickle.dump(model, f)
    logger.info(f"Markov model saved to {active_model}.")


def load_markov_model() -> markovify.NewlineText | None:
    global model  # noqa: PLW0603

    if not model:
        try:
            with active_model.open("rb") as f:
                model = pickle.load(f)  # noqa: S301
            logger.info(f"Markov model loaded from {active_model}.")
        except FileNotFoundError:
            logger.exception(f"{active_model} is not found!")
            return None

    return model
