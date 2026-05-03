import discord
from discord.ext import commands
from discord import app_commands

import discord.ext
import discord.ext.commands

import random

from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
from typing import TypedDict, List

class SettingsType(TypedDict):
    medias: List[str]
    reacts: bool
    chance: int

default_settings: SettingsType = {
    "medias": [],
    "reacts": True,
    "chance": 4000
}

class Share(commands.Cog): 
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = bot
        self.description = "?"

    @requires_admin()
    @commands.command()
    async def add_media(self, ctx: commands.Context, link: str):
        if link is None:
            await send_message(ctx, "Please specify a link!")
            return
        
        if not link.startswith(("http://", "https://")):
            await send_message(ctx, "Please specify a valid link with https://")
            return

        settings: SettingsType = settings_manager.get_plugin_settings("share", default=default_settings) #type: ignore[assignment]

        if link in settings.medias:
            await send_message(ctx, "Image is already in medias!")
            return
        
        settings.medias.append(link)
        settings_manager.set_plugin_setting("share", settings)
        await send_message(ctx, message=f"Added media!")


    @requires_admin()
    @commands.command()
    async def remove_media(self, ctx: commands.Context, link: str):
        if link is None:
            await send_message(ctx, "Please specify a link!")
            return
        
        if not link.startswith(("http://", "https://")):
            await send_message(ctx, "Please specify a valid link with https://")
            return

        settings: SettingsType = settings_manager.get_plugin_settings("share", default=default_settings) #type: ignore[assignment]

        if link not in settings.medias:
            await send_message(ctx, "Image isn't in medias!")
            return
        
        settings.medias.remove(link)
        settings_manager.set_plugin_setting("share", settings)

        await send_message(ctx, message=f"Removed media!")

    @commands.command()
    async def send_media(self, ctx: commands.Context):
        settings: SettingsType = settings_manager.get_plugin_settings("share", default=default_settings) #type: ignore[assignment]
        await send_message(ctx, random.choice(settings.medias))

    @requires_admin()
    @commands.command()
    async def list_media(self, ctx: commands.Context):
        settings: SettingsType = settings_manager.get_plugin_settings("share", default=default_settings) #type: ignore[assignment]
        message: str = "\n".join(settings.medias)

        await send_message(ctx, message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        settings: SettingsType = settings_manager.get_plugin_settings("share", default=default_settings) #type: ignore[assignment]

        if not settings.reacts: return

        if len(message.content) > 10 and random.randint(0, settings.chance) == 1:
            await message.reply(random.choice(settings.medias))


async def setup(bot):
    await bot.add_cog(Share(bot))
