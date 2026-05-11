import discord
from discord.ext import commands


class WhoAmI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = "Who Am I?"
        self.description = "👤 | A command to show your user information"

    @commands.hybrid_command(description="Show your user information")
    async def whoami(self, ctx: commands.Context):
        user_id = ctx.author.id
        username = ctx.author.name

        embed = discord.Embed(
            title="User Information",
            description=f"Your User ID is: {user_id}\n"
            f"Your username is: {username}\n"
            f"Your nickname in this server is: <@{user_id}>",
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WhoAmI(bot))
