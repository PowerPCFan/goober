from discord.ext import commands
from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.sync_connector import instance as synchub
from modules.settings import instance as settings_manager

settings = settings_manager.settings


class SyncHubManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = "Sync Hub"
        self.description = "📨|Commands for managing Goober Sync Hub"

    @requires_admin()
    @commands.command()
    async def synchub_test(self, ctx: commands.Context, message_id: str | None) -> None:
        message_id = message_id or "0"
        status = synchub.can_react(int(message_id), 0)

        await send_message(ctx, f"Allowed to react to message {message_id}? {'yes' if status else 'no'} (connection to {settings.bot.sync_hub.url} active? {'yes' if synchub.connected else 'no'})")

    @requires_admin()
    @commands.command()
    async def synchub_connect(self, ctx: commands.Context) -> None:
        await send_message(ctx, "Trying to connect...")

        connected = synchub.try_to_connect()
        if connected:
            await send_message(ctx, "Succesfully connected to sync hub!")
        else:
            await send_message(ctx, "Failed to connect to sync hub")

    @requires_admin()
    @commands.command()
    async def synchub_stats(self, ctx: commands.Context) -> None:
        connected = synchub.get_connected()
        await ctx.send(connected)


async def setup(bot: commands.Bot):
    print("Setting up synchub_management")
    await bot.add_cog(SyncHubManagement(bot))
