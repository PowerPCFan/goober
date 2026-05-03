import discord
from discord.ext import commands
from modules.globalvars import RED, GREEN, RESET
from modules.settings import ActivityType, instance as settings_manager
from modules.permission import requires_admin
from typing import get_args


class SongChanger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "🎧|Changes the bot's 'Listening to' status"

    @requires_admin()
    @commands.command()
    async def change_song(self, ctx, song: str):
        await ctx.send(f"Changed song to {song}")
        try:
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=f"{song}"
                )
            )
            print(f"{GREEN}Changed song to {song}{RESET}")
        except Exception as e:
            print(f"{RED}An error occurred while changing songs..: {str(e)}{RESET}")

    @requires_admin()
    @commands.command()
    async def change_activity(self, ctx: commands.Context, type: str | None, *string):
        if type not in get_args(ActivityType):
            await ctx.send(f"Type needs to be one of the following: {', '.join(get_args(ActivityType))}")
            return

        settings_manager.settings.bot.misc.activity = {
            "type": type,
            "content": ' '.join(string)
        }

        settings_manager.commit()

        activities: dict[ActivityType, discord.ActivityType] = {
            "listening": discord.ActivityType.listening,
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing,
            "watching": discord.ActivityType.watching,
        }

        await self.bot.change_presence(
            activity=discord.Activity(
                type=activities.get(
                    settings_manager.settings.bot.misc.activity.type,  # type: ignore
                    discord.ActivityType.unknown,
                ),
                name=settings_manager.settings.bot.misc.activity.content,
            )
        )

        await ctx.send("Changed activity!")


async def setup(bot: commands.Bot):
    await bot.add_cog(SongChanger(bot))
