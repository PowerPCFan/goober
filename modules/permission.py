import logging
import discord
import discord.ext
import discord.ext.commands
from modules.settings import instance as settings_manager

logger = logging.getLogger("goober")

settings = settings_manager.settings


class PermissionError(Exception):
    pass


def is_admin(id: int) -> bool:
    return id in settings.bot.owner_ids


def requires_admin():
    async def wrapper(ctx: discord.ext.commands.Context):
        if not is_admin(ctx.author.id):
            await ctx.send(
                "You don't have the necessary permissions to run this command!"
            )
            return False

        command = ctx.command
        if not command:
            logger.info(f"Unknown command ran {ctx.message}")
        else:
            logger.info(
                f'Command {settings.bot.prefix}{command.name} @{ctx.author.name}'
            )
        return True

    return discord.ext.commands.check(wrapper)
