import discord
from discord.ext import commands
import discord.ext
import discord.ext.commands
import math
import time
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
from typing import TypedDict
import requests_async
import logging
import datetime


class SettingsType(TypedDict):
    latitude: float
    longitude: float


default_settings: SettingsType = {
    "latitude": 30,
    "longitude": 0
}


class ThresholdValue(TypedDict):
    label: str
    emoji: str


CO2_THRESHOLDS: dict[int, ThresholdValue] = {
    400: {
        "label": "Great",
        "emoji": "🔵"
    },
    600: {
        "label": "Good",
        "emoji": "🟢"
    },
    800: {
        "label": "OK",
        "emoji": "🟢"
    },
    1000: {
        "label": "Suboptimal",
        "emoji": "🟡"
    },
    1300: {
        "label": "Bad",
        "emoji": "🔴"
    },
    1800: {
        "label": "Very bad",
        "emoji": "🟣"
    }
}

TEMP_THRESHOLDS: dict[int, ThresholdValue] = {
    16: {
        "label": "Cold",
        "emoji": "🔵"
    },
    18: {
        "label": "Optimal",
        "emoji": "🟢"
    },
    21: {
        "label": "Warm",
        "emoji": "🟡"
    },
    24: {
        "label": "Hot",
        "emoji": "🔴"
    }
}

HUMIDITY_THRESHOLDS: dict[int, ThresholdValue] = {
    0: {
        "label": "Too dry",
        "emoji": "🟡"
    },
    35: {
        "label": "Optimal",
        "emoji": "🟢"
    },
    65: {
        "label": "Too damp",
        "emoji": "🟡"
    }
}

RESISTANCE_THRESHOLDS: dict[int, ThresholdValue] = {
    20_000: {
        "label": "Bad",
        "emoji": "🟡"
    },
    90_000: {
        "label": "OK",
        "emoji": "🟡"
    },
    120_000: {
        "label": "Good",
        "emoji": "🟢"
    }
}

PM25_THRESHOLDS: dict[int, ThresholdValue] = {
    0: {
        "label": "Excellent",
        "emoji": "🔵"
    },
    6: {
        "label": "Good",
        "emoji": "🟢"
    },
    12: {
        "label": "OK",
        "emoji": "🟡"
    },
    35: {
        "label": "Unhealthy",
        "emoji": "🔴"
    },
    60: {
        "label": "Very unhealthy",
        "emoji": "🟣"
    }
}

PM100_THRESHOLDS: dict[int, ThresholdValue] = {
    0: {
        "label": "Excellent",
        "emoji": "🔵"
    },
    12: {
        "label": "Good",
        "emoji": "🟢"
    },
    24: {
        "label": "OK",
        "emoji": "🟡"
    },
    75: {
        "label": "Unhealthy",
        "emoji": "🔴"
    },
    120: {
        "label": "Very unhealthy",
        "emoji": "🟣"
    }
}

OUTDOOR_TEMP_THRESHOLDS: dict[int, ThresholdValue] = {
    -50: {
        "label": "Extremely frigid",
        "emoji": "⚫"
    },
    -25: {
        "label": "Very frigid",
        "emoji": "🟣"
    },
    -20: {
        "label": "Very cold",
        "emoji": "🔵"
    },
    -15: {
        "label": "Cold",
        "emoji": "🔵"
    },
    -10: {
        "label": "Mildly cold",
        "emoji": "🔵"
    },
    -5: {
        "label": "Chilly",
        "emoji": "⚪"
    },
    0: {
        "label": "Cool",
        "emoji": "⚪"
    },
    5: {
        "label": "Brisk",
        "emoji": "🟢"
    },
    10: {
        "label": "Mild",
        "emoji": "🟢"
    },
    15: {
        "label": "Warm",
        "emoji": "🟡"
    },
    20: {
        "label": "Very warm",
        "emoji": "🟡"
    },
    25: {
        "label": "Hot",
        "emoji": "🟠"
    },
    30: {
        "label": "Very hot",
        "emoji": "🔴"
    }
}

OUTDOOR_HUMIDITY_THRESHOLDS: dict[int, ThresholdValue] = {
    0: {
        "label": "Extremely dry",
        "emoji": "🟠"
    },
    15: {
        "label": "Very dry",
        "emoji": "🟠"
    },
    30: {
        "label": "Dry",
        "emoji": "🟡"
    },
    50: {
        "label": "Comfortable",
        "emoji": "🟢"
    },
    65: {
        "label": "Slightly humid",
        "emoji": "🟢"
    },
    75: {
        "label": "Humid",
        "emoji": "🔵"
    },
    85: {
        "label": "Very humid",
        "emoji": "🔵"
    },
    95: {
        "label": "Extremely humid",
        "emoji": "🟣"
    }
}

SUN_POSITION_THRESHOLD: dict[int, ThresholdValue] = {
    -100: {
        "label": "Night",
        "emoji": "🌌"
    },
    -18: {
        "label": "Astronomical twilight",
        "emoji": "🌙"
    },
    -12: {
        "label": "Nautical twilight",
        "emoji": "⭐"
    },
    -6: {
        "label": "Civil twilight",
        "emoji": "🌃"
    },
    -2: {
        "label": "Sunrise or -set",
        "emoji": "🌅"
    },
    2: {
        "label": "Day",
        "emoji": "☀️"
    }
}

PRESSURE_THRESHOLDS: dict[int, ThresholdValue] = {
    900: {
        "label": "Extremely low pressure",
        "emoji": "🔴"
    },
    980: {
        "label": "Very low pressure",
        "emoji": "🟠"
    },
    995: {
        "label": "Low pressure",
        "emoji": "🟡"
    },
    1005: {
        "label": "Normal pressure",
        "emoji": "🟢"
    },
    1015: {
        "label": "High pressure",
        "emoji": "🔵"
    },
    1025: {
        "label": "Very high pressure",
        "emoji": "🟣"
    }
}

logger = logging.getLogger("goober")


class Indoor(TypedDict):
    time: str
    temperature: float
    humidity: float
    pressure: float
    gas: float
    pm1_0: float
    pm2_5: float
    pm10_0: float
    vocs: float
    carbon_dioxide: float
    wifi_strength: float
    aqi: int


class Climate(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = bot
        self.description = "🌱|Monitor my indoor and outdoor climates"

    def get_ranking(self, current_value: float, thresholds: dict[int, ThresholdValue]) -> ThresholdValue:
        found_threshold: ThresholdValue = {
            "emoji": "",
            "label": ""
        }

        for value, threshold in sorted(thresholds.items(), key=lambda item: item[0]):
            logger.info(str(current_value) + " " + str(value))
            if current_value < value:
                break

            found_threshold = threshold

        return found_threshold

    def format_embed(self, label: str, unit: str, value: float, threshold: dict[int, ThresholdValue]) -> dict:
        ranking = self.get_ranking(value, threshold)
        return {
            "name": f"{label} {ranking['emoji']}",
            "value": f"{round(value, 2)} {unit} (**{ranking['label']}**)"
        }

    def get_sun_angle(self) -> float:
        settings: SettingsType = settings_manager.get_plugin_settings("climate", default_settings)  # type: ignore

        now = datetime.datetime.now()
        hour = now.hour + now.minute / 60 + now.second / 3600
        solar_hour = hour + (settings["longitude"] + 60) / 15  # +60 for UTC-4 timezone
        nth_day_of_year = (now - datetime.datetime(now.year, 1, 1)).days + 1
        declination = math.radians(23.445 * math.sin(math.radians((360 / 365.25) * (nth_day_of_year - 81))))
        hour_angle = math.radians(15 * (solar_hour - 12))

        result = math.degrees(math.asin(
            math.sin(declination)
            * math.sin(math.radians(settings["latitude"]))
            + math.cos(declination)
            * math.cos(math.radians(settings["latitude"]))
            * math.cos(hour_angle)
        ))

        if result > -1.0:
            refraction = 1.02 / math.tan(math.radians(result + 10.3 / (result + 5.11))) / 60
            result += refraction

        return result

    @commands.command()
    async def indoors(self, ctx: commands.Context):
        res = await requests_async.get("http://192.168.1.45:8080/latest/indoor")
        data: Indoor = res.json()

        embed = discord.Embed(
            title="Climate data",
            description="Information about my indoor climate"
        )

        isotime = str(data.get("time", "1970-01-01T00:00:00+00:00"))
        try:
            timestamp = int(datetime.datetime.fromisoformat(isotime).timestamp())
        except ValueError:
            timestamp = 0

        embed.add_field(**self.format_embed("CO2", "PPM", data['carbon_dioxide'], CO2_THRESHOLDS))
        embed.add_field(**self.format_embed("Temperature", "°F", data["temperature"] * 9/5 + 32, TEMP_THRESHOLDS))
        embed.add_field(**self.format_embed("Humidity", "%RH", data["humidity"], HUMIDITY_THRESHOLDS))
        embed.add_field(**self.format_embed("Gas", "kΩ", data['gas'], RESISTANCE_THRESHOLDS))
        embed.add_field(**self.format_embed("Pressure", "inHg", data['pressure'] * 0.02953, PRESSURE_THRESHOLDS))
        embed.add_field(**self.format_embed("PM1.0", "µg/m³", data['pm1_0'], PM25_THRESHOLDS))
        embed.add_field(**self.format_embed("PM2.5", "µg/m³", data['pm2_5'], PM25_THRESHOLDS))
        embed.add_field(**self.format_embed("PM10.0", "µg/m³", data['pm10_0'], PM100_THRESHOLDS))

        embed.set_footer(text=f"Last updated: {time.strftime('%H:%M:%S %d/%m/%Y', time.gmtime(timestamp))} (UTC)")

        await send_message(ctx, embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Climate(bot))
