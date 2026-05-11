import json
import logging
import pickle

import markovify

from modules.globalvars import RESET
from modules.settings import instance as settings_manager

settings = settings_manager.settings

model: markovify.NewlineText | None = None

logger = logging.getLogger("goober")


def load_memory():
    data = []

    try:
        with open(settings.bot.active_memory, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(settings.bot.active_memory, "w") as f:
            json.dump([], f)
            data = []

    return data


def save_memory(memory):
    with open(settings.bot.active_memory, "w") as f:
        json.dump(memory, f, indent=4)


def train_markov_model(memory, additional_data=None) -> markovify.NewlineText | None:
    if not memory:
        return None

    filtered_memory = [line for line in memory if isinstance(line, str)]
    if additional_data:
        filtered_memory.extend(line for line in additional_data if isinstance(line, str))

    if not filtered_memory:
        return None

    text = "\n".join(filtered_memory)
    model = markovify.NewlineText(text, state_size=2)
    return model


def save_markov_model(model):
    filename = settings.bot.active_model

    with open(filename, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Markov model saved to {filename}.")


def load_markov_model():
    global model
    filename = settings.bot.active_model

    if not model:
        try:
            with open(filename, "rb") as f:
                model = pickle.load(f)
            logger.info(f"Markov model loaded from {filename}.{RESET}")
        except FileNotFoundError:
            logger.error(f"{filename} is not found!{RESET}")
            return None

    return model
