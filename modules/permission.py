import logging
import discord
import discord.ext
import discord.ext.commands
from modules.embeds import send_error
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
            await send_error(
                ctx,
                title="Permission Denied",
                description="You don't have the necessary permissions to run this command!"
            )
            return False

        if not ctx.command:
            logger.info(f"Unknown command ran: {ctx.command} ran by @{ctx.author.name} (message: {ctx.message})")
        else:
            logger.info(
                f'Command {settings.bot.prefix}{ctx.command.name} ran by @{ctx.author.name}'
            )
        return True

    return discord.ext.commands.check(wrapper)
