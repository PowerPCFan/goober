import logging
from typing import Any

from discord.ext import commands
from discord.ext.commands._types import Check

from modules.embeds import send_error
from modules.settings import instance as settings_manager

logger = logging.getLogger("goober")

settings = settings_manager.settings


def is_admin(user_id: int) -> bool:
    return user_id in settings.bot.owner_ids


def requires_admin() -> Check[commands.Context[Any]]:
    async def wrapper(ctx: commands.Context) -> bool:
        if not is_admin(ctx.author.id):
            await send_error(
                ctx,
                title="Permission Denied",
                description="You don't have the necessary permissions to run this command!",
            )
            return False

        if not ctx.command:
            logger.info(f"Unknown admin command '{ctx.command}' ran by @{ctx.author.name}")
        else:
            logger.info(f"Admin command '{ctx.command.name}' ran by @{ctx.author.name}")

        return True

    return commands.check(wrapper)
