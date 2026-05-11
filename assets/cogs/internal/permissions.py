import discord
from discord.ext import commands

from modules.permission import requires_admin
from modules.settings import instance as settings_manager

settings = settings_manager.settings


class PermissionManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = "Permission Manager"
        self.description = "🔐 | Commands for managing bot permissions"

    @requires_admin()
    @commands.hybrid_command(description="Add a user as a bot owner")
    async def add_owner(self, ctx: commands.Context, member: discord.Member):
        settings.bot.owner_ids.append(member.id)
        settings_manager.add_admin_log_event(
            {
                "action": "add",
                "author": ctx.author.id,
                "change": "owner_ids",
                "messageId": ctx.message.id,
                "target": member.id,
            }
        )

        settings_manager.commit()

        embed = discord.Embed(
            title="Permissions",
            description=f"Set {member.name} as an owner",
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)

    @requires_admin()
    @commands.hybrid_command(description="Remove a user from bot owner privileges")
    async def remove_owner(self, ctx: commands.Context, member: discord.Member):
        try:
            settings.bot.owner_ids.remove(member.id)
            settings_manager.add_admin_log_event(
                {
                    "action": "del",
                    "author": ctx.author.id,
                    "change": "owner_ids",
                    "messageId": ctx.message.id,
                    "target": member.id,
                }
            )
            settings_manager.commit()
        except ValueError:
            await ctx.send("User is not an owner!")
            return

        embed = discord.Embed(
            title="Permissions",
            description=f"Removed {member.name} from being an owner",
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)

    @requires_admin()
    @commands.hybrid_command(description="Blacklist a user from using the bot")
    async def blacklist_user(self, ctx: commands.Context, member: discord.Member):
        settings.bot.blacklisted_users.append(member.id)
        settings_manager.add_admin_log_event(
            {
                "action": "add",
                "author": ctx.author.id,
                "change": "blacklisted_users",
                "messageId": ctx.message.id,
                "target": member.id,
            }
        )
        settings_manager.commit()

        embed = discord.Embed(
            title="Blacklist",
            description=f"Added {member.name} to the blacklist",
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)

    @requires_admin()
    @commands.hybrid_command(description="Unblacklist a user to allow them to use the bot")
    async def unblacklist_user(self, ctx: commands.Context, member: discord.Member):
        try:
            settings.bot.blacklisted_users.remove(member.id)
            settings_manager.add_admin_log_event(
                {
                    "action": "del",
                    "author": ctx.author.id,
                    "change": "blacklisted_users",
                    "messageId": ctx.message.id,
                    "target": member.id,
                }
            )
            settings_manager.commit()

        except ValueError:
            await ctx.send("User is not on the blacklist!")
            return

        embed = discord.Embed(
            title="Blacklist",
            description=f"Removed {member.name} from blacklist",
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PermissionManager(bot))
