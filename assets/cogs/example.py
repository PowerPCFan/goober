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

# Name according to your cog (e.g a random number generator -> RandomNumber)
class Example(commands.Cog): 
    # __init__ method is required with these exact parameters
    def __init__(self, bot: discord.ext.commands.Bot): # type hinting (aka : discord.ext.commands.Bot) isn't necessary, but provides better intellisense in code editors
        self.bot: discord.ext.commands.Bot = bot


    # a basic ping slash command which utilizes embeds
    @app_commands.command(name="ping", description="A command that sends a ping!")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()

        example_embed = discord.Embed(
            title="Pong!!",
            description="The Beretta fires fast and won't make you feel any better!",
            color=discord.Color.blue(),
        )
        example_embed.set_footer(
            text=f"Requested by {interaction.user.name}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.followup.send(embed=example_embed)

    # a basic command (aka prefix.random_number)
    # Shows how to get parameters, and how to send messages using goobers message thing
    @commands.command()
    async def random_number(self, ctx: commands.Context, minimum: int | None, maximum: int | None): # every argument after ctx is a part of the command, aka "g.random_number 0 5" would set minimum as 0 and maximum as 5
                                                                                                    # We should always assume that command parameters are None, since someone can gall g.randon_number. 

        if minimum is None:
            await send_message(ctx, message="Please specify the minimum number!")
            return # make sure we dont continue 
        
        if maximum is None:
            await send_message(ctx, message="Please specify the maximum number!")
            return # make sure we dont continue 
        
        
        number = random.randint(minimum, maximum)

        example_embed = discord.Embed(
            title="Random number generator",
            description=f"Random number: {number}",
            color=discord.Color.blue(),
        )
        example_embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar,
        )

        await send_message(ctx, embed=example_embed)


    # A command which requires the executor to be an admin, and takes a discord user as an argument
    @requires_admin() # from modules.permission import requires_admin
    @commands.command()
    async def ban_user(self, ctx: commands.Context, target: discord.Member | None, reason: str | None):
        if target is None:
            await send_message(ctx, "Please specify a user by pinging them!")
            return
        
        await target.ban(reason=reason)
        await send_message(ctx, message=f"Banned user {target.name}!")


    # Changing and getting plugin settings, defining a settings schmea
    @commands.command()
    async def change_hello_message(self, ctx: commands.Context, new_message: str | None):
        COG_NAME = "example" # change this to whatever you want, but keep it the same accross your cog

        if new_message is None:
            await send_message(ctx, "Please specify a new message!")
            return
        
        # Generating a settings schema (optional)
        # from typing import TypedDict
        class IntroSettings(TypedDict):
            message: str

        class SettingsType(TypedDict): 
            intro: IntroSettings
            leave_message: str

        # End of optional typing
        # Note: if you decide to do this, please place these at the top of the file! (but after imports)
        
        default_settings: SettingsType = { # use default_settings = { if you didnt define the types
            "intro": {
                "message": "Hello user!"
            },
            "leave_message": "Goodbye user!"
        }


        # from modules.settings import instance as settings_manager
        # get current plugin settings
        # change "example" to your cog name
        settings: SettingsType = settings_manager.get_plugin_settings(COG_NAME, default=default_settings) #type: ignore[assignment]
    
        # Now you can use settings easily!

        current_message = settings.intro.message
        await send_message(ctx, message=f"Current message: {current_message}")

        # Changing plugin settings
        settings.intro.message = "brand new message!"

        settings_manager.set_plugin_setting(COG_NAME, settings)

        new_message = settings.intro.message
        await send_message(ctx, message=f"New message: {new_message}")



async def setup(bot):
    await bot.add_cog(Example(bot))
