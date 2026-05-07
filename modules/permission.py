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

        if not ctx.command:
            logger.info(f"Unknown command ran {ctx.message}")
        else:
            logger.info(
                f'Command {settings.bot.prefix}{ctx.command.name} @{ctx.author.name}'
            )
        return True

    return discord.ext.commands.check(wrapper)


def requires_admin_slashcommand():
    async def wrapper(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                "You don't have the necessary permissions to run this command!",
                ephemeral=True
            )
            return False

        if not interaction.command:
            logger.info(f"Unknown command ran {interaction.message}")
        else:
            logger.info(
                f'Command {settings.bot.prefix}{interaction.command.name} @{interaction.user.name}'
            )
        return True

    return discord.app_commands.check(wrapper)
