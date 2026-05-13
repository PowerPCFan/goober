from discord.ext import commands

from modules.permission import requires_admin
from modules.settings import instance as settings_manager
from modules.sync_connector import instance as synchub

settings = settings_manager.settings


class SyncHubManagement(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.name = "Sync Hub"
        self.description = "📨|Commands for managing Goober Sync Hub"

    @requires_admin()
    @commands.hybrid_command(description="Test sync hub message reaction permissions")
    async def synchub_test(self, ctx: commands.Context, message_id: str | None) -> None:
        message_id = message_id or "0"
        status = synchub.can_react(int(message_id), 0)

        await ctx.send(f"Allowed to react to message {message_id}? {'yes' if status else 'no'} (connection to {settings.bot.sync_hub.url} active? {'yes' if synchub.connected else 'no'})")  # noqa: E501

    @requires_admin()
    @commands.hybrid_command(description="Connect to the sync hub")
    async def synchub_connect(self, ctx: commands.Context) -> None:
        await ctx.send("Trying to connect...")

        connected = synchub.try_to_connect()
        if connected:
            await ctx.send("Succesfully connected to sync hub!")
        else:
            await ctx.send("Failed to connect to sync hub")

    @requires_admin()
    @commands.hybrid_command(description="View sync hub connection statistics")
    async def synchub_stats(self, ctx: commands.Context) -> None:
        connected = synchub.get_connected()
        await ctx.send(connected)


async def setup(bot: commands.Bot) -> None:
    print("Setting up synchub_management")
    await bot.add_cog(SyncHubManagement(bot))
