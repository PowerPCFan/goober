import random
from discord.ext import commands


class Eightball(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "🎱|It is certainly an 8-ball"

    @commands.command()
    async def eightball(self, ctx: commands.Context):
        answer = random.choice(
            [
                "It is certain.",
                "It is decidedly so.",
                "Without a doubt.",
                "Yes definitely.",
                "You may rely on it.",
                "As I see it, yes.",
                "Most likely.",
                "Outlook good.",
                "Yes.",
                "Signs point to yes.",
                "Reply hazy, try again.",
                "Ask again later.",
                "Better not tell you now.",
                "Cannot predict now.",
                "Concentrate and ask again.",
                "Don't count on it.",
                "My reply is no.",
                "My sources say no.",
                "Outlook not so good.",
                "Very doubtful.",
            ]
        )

        await ctx.send(answer)


async def setup(bot: commands.Bot):
    await bot.add_cog(Eightball(bot))
