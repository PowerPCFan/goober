import sys
import logging
import traceback
import discord
from discord.ext.commands import Context
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager

settings = settings_manager.settings
logger = logging.getLogger("goober")


def handle_exception(exc_type, exc_value, exc_traceback, *, context: str | None = None):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("=====BEGINNING OF TRACEBACK=====")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    logger.error("========END OF TRACEBACK========")
    logger.error('An unhandled exception occurred. Please report this issue on GitHub.')

    if context:
        logger.error(f"Context: {context}")


async def handle_exception_with_context(ctx: Context, exc_type, exc_value, exc_traceback, *, context: str | None = None):
    handle_exception(exc_type, exc_value, exc_traceback, context=context)

    embed = discord.Embed(color=0xfc1c03)
    embed.title = "Command failed with exception"
    embed.description = "```" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))[-4000:] + "```"

    await send_message(ctx, embed=embed)
