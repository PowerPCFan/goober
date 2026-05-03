import discord
from discord.ext import commands
import cpuinfo
import psutil
import platform


class Flex(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "💪|Flex your machine!!"

    @commands.command()
    async def flex(self, ctx: commands.Context):
        cpu: dict = cpuinfo.get_cpu_info()
        cpu_name = cpu["brand_raw"]
        threads = int(cpu["count"])

        temp = -99.99
        if platform.system() == "Linux":
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = int(f.read()) / 1000

        embed = discord.Embed(
            title="Flex",
            description="Some useful information about the device",
            color=discord.Color.blue()
        )

        embed.add_field(name="Network", value=f"`{platform.node()}`")
        embed.add_field(name="CPU", value=f"`{cpu_name}` with {threads} threads")
        embed.add_field(name="CPU utilization", value=f"{round(psutil.cpu_percent(), 2)}%")
        embed.add_field(name="CPU temperature", value=f"{round(temp, 1)}*C")
        embed.add_field(name="Installed RAM", value=f"`{round(psutil.virtual_memory().total / 1024 / 1024)}MB`")
        embed.add_field(name="Platform", value=f"`{platform.platform()}`")
        embed.add_field(name="Python", value=f"{platform.python_version()}")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Flex(bot))
