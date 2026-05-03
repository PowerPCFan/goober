import discord
from discord.ext import commands
from modules.globalvars import RED, GREEN, RESET, LOCAL_VERSION_FILE
import os
from modules.settings import ActivityType, instance as settings_manager
from modules.permission import requires_admin

from typing import get_args, Dict


class SongChanger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "🎧|Changes the bot's 'Listening to' status"


    def get_local_version():
        if os.path.exists(LOCAL_VERSION_FILE):
            with open(LOCAL_VERSION_FILE, "r") as f:
                return f.read().strip()
        return "0.0.0"

    global local_version
    local_version = get_local_version()

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
    async def change_activity(self, ctx, type: str | None, *string):
        if type not in get_args(ActivityType):
            await ctx.send(f"Type needs to be one of the following: {', '.join(get_args(ActivityType))}")
            return 
        
        settings_manager.settings.bot.misc.activity = { # type: ignore
            "type": type,
            "content": ' '.join(string)
        }

        settings_manager.commit()

            
        activities: Dict[ActivityType, discord.ActivityType] = {
            "listening": discord.ActivityType.listening,
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing,
            "watching": discord.ActivityType.watching,
        }

        await self.bot.change_presence(
            activity=discord.Activity(
                type=activities.get(
                    settings_manager.settings.bot.misc.activity.type, # type: ignore
                    discord.ActivityType.unknown,
                ),
                name=settings_manager.settings.bot.misc.activity.content,
            )
        )

        await ctx.send("Changed activity!")

async def setup(bot):
    await bot.add_cog(SongChanger(bot))
