import discord
from discord.ext import commands

from modules.embeds import send_error, send_info, send_success
from modules.globalvars import available_cogs
from modules.permission import requires_admin
from modules.settings import instance as settings_manager

settings = settings_manager.settings


COG_PREFIX = "assets.cogs."


class CogManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.name = "Cog Management"
        self.description = "💼|Commands for managing cogs"

    @requires_admin()
    @commands.hybrid_command(description="Enable a cog")
    async def enable(self, ctx: commands.Context, cog_name: str) -> None:
        try:
            await self.bot.load_extension(COG_PREFIX + cog_name)
            await send_success(
                ctx,
                title="Cog Enabled",
                description=f"Enabled cog `{cog_name}` successfully.",
            )
            settings.bot.disabled_cogs.remove(cog_name)
            settings_manager.add_admin_log_event(
                {
                    "action": "del",
                    "author": ctx.author.id,
                    "change": "disabled_cogs",
                    "message_id": ctx.message.id,
                    "target": cog_name,
                },
            )
            settings_manager.commit()

        except Exception as e:
            await send_error(ctx, description=f"Error enabling cog `{cog_name}`: {e}")

    @requires_admin()
    @commands.hybrid_command(description="Load a cog")
    async def load(self, ctx: commands.Context, cog_name: str | None = None) -> None:
        if cog_name is None:
            await send_error(ctx, description="Please provide the cog name to load.")
            return

        try:
            await self.bot.load_extension(COG_PREFIX + cog_name)
            await send_success(
                ctx,
                title="Cog Loaded",
                description=f"Loaded cog `{cog_name}` successfully.",
            )
        except Exception as e:
            await send_error(ctx, description=f"Error loading cog `{cog_name}`: {e}")

    @requires_admin()
    @commands.hybrid_command(description="Unload a cog")
    async def unload(self, ctx: commands.Context, cog_name: str | None = None) -> None:
        if cog_name is None:
            await send_error(ctx, description="Please provide the cog name to unload.")
            return
        try:
            await self.bot.unload_extension(COG_PREFIX + cog_name)
            await send_success(
                ctx,
                title="Cog Unloaded",
                description=f"Unloaded cog `{cog_name}` successfully.",
            )
        except Exception as e:
            await send_error(ctx, description=f"Error unloading cog `{cog_name}`: {e}")

    @requires_admin()
    @commands.hybrid_command(description="Disable a cog")
    async def disable(self, ctx: commands.Context, cog_name: str | None = None) -> None:
        if cog_name is None:
            await send_error(ctx, description="Please provide the cog name to disable.")
            return
        try:
            await self.bot.unload_extension(COG_PREFIX + cog_name)
            await send_success(
                ctx,
                title="Cog Disabled",
                description=f"Disabled cog `{cog_name}` successfully.",
            )
            settings.bot.disabled_cogs.append(cog_name)
            settings_manager.add_admin_log_event(
                {
                    "action": "add",
                    "author": ctx.author.id,
                    "change": "disabled_cogs",
                    "message_id": ctx.message.id,
                    "target": cog_name,
                },
            )
            settings_manager.commit()
        except Exception as e:
            await send_error(ctx, description=f"Error disabling cog `{cog_name}`: {e}")

    @requires_admin()
    @commands.hybrid_command(description="Reload a cog")
    async def reload(self, ctx: commands.Context, cog_name: str | None = None) -> None:
        if cog_name is None:
            await send_error(ctx, description="Please provide the cog name to reload.")
            return

        try:
            await self.bot.unload_extension(COG_PREFIX + cog_name)
            await self.bot.load_extension(COG_PREFIX + cog_name)
            await send_success(
                ctx,
                title="Cog Reloaded",
                description=f"Reloaded cog `{cog_name}` successfully.",
            )
        except Exception as e:
            await send_error(ctx, description=f"Error reloading cog `{cog_name}`: {e}")

    @commands.hybrid_command(description="List all loaded and available cogs")
    async def listcogs(self, ctx: commands.Context) -> None:
        cogs = list(self.bot.cogs.keys())
        if not cogs:
            await send_info(
                ctx,
                title="No Cogs Loaded",
                description="No cogs are currently loaded.",
            )
            return

        embed = discord.Embed(
            title="Loaded Cogs",
            description="Here is a list of all currently loaded cogs:",
        )
        embed.add_field(name="Loaded cogs", value="\n".join(cogs), inline=False)
        embed.add_field(name="Available cogs", value="\n".join(available_cogs))
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CogManager(bot))
