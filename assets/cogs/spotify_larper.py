import discord
from discord.ext import commands
from discord import app_commands

import discord.ext
import discord.ext.commands
import time
import random
from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
from typing import TypedDict, List
import logging
from modules.helpers.lrclib import LRCAPI, LRCLIBFetchResponse, LRCLIBResponse


logger = logging.getLogger("goober")

class SettingsType(TypedDict):
    followed_user: int

default_settings: SettingsType = {
    "followed_user": settings_manager.settings.bot.owner_ids[0]
}

class SpotifyLarper(commands.Cog): 
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = bot
        self.last_song_id: str = "0"
        self.last_request_time: float = 0
        self.current_activity: discord.activity.Spotify | None = None
        self.description = "📝|Sets the bot's RPC to be a random lyric from the song you're listening to"


    @requires_admin()
    @commands.command()
    async def follow(self, ctx: commands.Context, user: discord.Member):
        settings: SettingsType = settings_manager.get_plugin_settings("spotify_larper", default_settings) # type: ignore
        settings.followed_user = user.id
        settings_manager.set_plugin_setting("spotify_larper", settings)

        await send_message(ctx, f"Changed followed user to {user.mention}")

    @commands.command()
    async def now_larping(self, ctx: commands.Context):
        if self.current_activity is None:
            await send_message(ctx, "Currently not larping :sunglasses:")
            return
        
        await send_message(ctx, f"Currently larping \"{self.current_activity.title}\" by {self.current_activity.artist}")
        await send_message(ctx, self.current_activity.album_cover_url)

    
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        settings: SettingsType = settings_manager.get_plugin_settings("spotify_larper", default_settings) # type: ignore
        
        if after.id != settings.followed_user:
            return
        

        logger.debug("User changed status! Checking for activity")
        target_activity: discord.activity.Spotify | None = None
        for activity in after.activities:
            if not isinstance(activity, discord.activity.Spotify): continue

            target_activity = activity
            break

        if target_activity is None:
            logger.debug("No Spotify activity")
            return
        
        if target_activity.track_id == self.last_song_id:
            logger.debug("Same track ID; skipping")
            return
        
        if time.time() - self.last_request_time < 12:
            logger.debug("Request too close, skipping")
            return

        self.last_song_id = target_activity.track_id
        self.last_request_time = time.time()
        matches: List[LRCLIBResponse] = await LRCAPI.search_song(f"{target_activity.title} {target_activity.artist}")

        if len(matches) == 0:
            logger.info("Could not find lyrics")

        matched_lyrics: str = ""
        for match in matches:
            if target_activity.artist.lower() in match["artistName"].lower() or abs(match["duration"] - target_activity.duration.total_seconds()) < 10:
                matched_lyrics = match["plainLyrics"]
                break
            
        if not matched_lyrics:
            logger.info("Could not find accurate lyrics")
            return
        
        lyrics: List[str] = matched_lyrics.split("\n")

        logger.info(f"Found song with {len(lyrics)} lyrics")
        lyric: str = ""

        suitable_lyrics = [lyric for lyric in lyrics if len(lyric) > 5 and len(lyric) < 30 and len(set(lyric)) > 4 and "?" in lyric]
        
        if len(suitable_lyrics) >= 1:
            logger.info("Found suitable lyric")
            lyric = random.choice(suitable_lyrics)
        else:
            logger.info("Couldnt find suitable lyric, randomizing...")
            for _ in range(500):
                lyric = random.choice(lyrics)

                if len(lyric) > 5 and len(lyric) < 30 and len(set(lyric)) >= 4:
                    break

        if lyric == "":
            logger.info("Could not find a good enough lyric, skipping")
            return

        self.current_activity = target_activity

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f'"{lyric}"',
            )
        )

        logger.info("Changed activity!")


async def setup(bot):
    await bot.add_cog(SpotifyLarper(bot))
