import discord
from discord.ext import commands
from discord import app_commands

import discord.ext
import discord.ext.commands

import random

from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
from typing import TypedDict
import logging

import unalix

logger = logging.getLogger("goober")

class LinkCleanerSettings(TypedDict):
    automatic: bool

DEFAULT: LinkCleanerSettings = {
    "automatic": False
}

class LinkCleaner(commands.Cog): 
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = bot
        self.description = "✂|Removes tracking URLs from links"


    @commands.command()
    async def enable_automatic_cleaning(self, ctx: commands.Context, enabled: str | None):
        if enabled is None:
            await ctx.send(f"Please use {settings_manager.settings.bot.prefix}enable_automatic_cleaning <yes | no>")
            return
        
        new_mode: bool = enabled.lower() == "yes"

        settings: LinkCleanerSettings = settings_manager.get_plugin_settings("link_cleaner", DEFAULT) # type: ignore
        settings.automatic = new_mode
        
        if new_mode == True:
            await ctx.send("Enabled automatic link cleaning!")
            return
        else:
            await ctx.send("Disabled automatic link cleaning!")

    @commands.command()
    async def clean(self, ctx: commands.Context, link: str | None):
        if link is None:
            await ctx.send(f"Please specify a link!")
            return

        await ctx.reply(unalix.clear_url(link))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if "http" not in message.content:
            logger.debug("Skipping message, does not contain a link")
            return
        
        if not settings_manager.get_plugin_settings("link_cleaner", DEFAULT).get("automatic"):
            logger.debug("Automation not enabled in plugin settings")
            return

        for element in message.content.split():
            if not element.startswith("http"):
                continue

            await message.reply(unalix.clear_url(element))
            break

            
async def setup(bot):
    await bot.add_cog(LinkCleaner(bot))
