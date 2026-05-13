import logging
import re
import sys
import threading

import spacy
from spacy.tokens import Doc

from modules.globalvars import RESET

logger = logging.getLogger("goober")
nlp: spacy.language.Language | None = None


def check_resources() -> None:
    global nlp  # noqa: PLW0603

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.critical("The spaCy model was not found! Downloading it....`")
        spacy.cli.download("en_core_web_sm")  # pyright: ignore[reportAttributeAccessIssue]
        nlp = spacy.load("en_core_web_sm")
    try:
        from spacytextblob.spacytextblob import SpacyTextBlob  # noqa: F401, PLC0415
    except Exception:
        logger.exception("spacytextblob is not available")
        return

    if "spacytextblob" not in nlp.pipe_names:
        try:
            nlp.add_pipe("spacytextblob")
        except ValueError:
            logger.exception("Failed to add spacytextblob")
            return

    if not Doc.has_extension("polarity"):
        Doc.set_extension("polarity", getter=lambda doc: doc._.blob.polarity)

    logger.info("spaCy and spacytextblob are ready.")


nlp_thread = threading.Thread(target=check_resources)
nlp_thread.start()


def is_positive(sentence: str) -> bool:
    nlp_thread.join()

    if nlp is None:
        logger.error("NLP Not loaded! Defaulting to positivity 0")
        return False

    doc = nlp(sentence)
    sentiment_score = doc._.polarity

    debug_message = f"Positivity of sentence is: {sentiment_score}{RESET}"
    logger.debug(debug_message)

    threshold = 0.6

    return sentiment_score > threshold


def append_mentions_to_18digit_integer(message: str) -> str:
    pattern = r"\b\d{18}\b"
    return re.sub(pattern, lambda match: "", message)  # noqa: ARG005


def preprocess_message(message: str) -> str:
    nlp_thread.join()
    message = append_mentions_to_18digit_integer(message)
    if nlp is None:
        logger.error("NLP not loaded! Quitting")
        sys.exit(1)

    doc = nlp(message)
    tokens = [token.text for token in doc if token.is_alpha or token.is_digit]
    return " ".join(tokens)


def improve_sentence_coherence(sentence: str) -> str:
    return re.sub(r"\bi\b", "I", sentence)


def rephrase_for_coherence(sentence: str) -> str:
    return " ".join(sentence.split())
