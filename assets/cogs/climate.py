import discord
from discord.ext import commands
import discord.ext
import discord.ext.commands
import math
import time
from modules.permission import requires_admin
from modules.sentenceprocessing import send_message
from modules.settings import instance as settings_manager
from typing import TypedDict, Dict
import requests_async
import logging
import datetime


# todo: finish making this work with my climate thingy


class SettingsType(TypedDict):
    latitude: float
    longtitude: float


default_settings: SettingsType = {
    "latitude": 30,
    "longtitude": 0
}


class IndoorData(TypedDict):
    temperature: float
    relative_humidity: float
    air_pressure: float
    air_resistance: float
    sensor_calibrated: bool
    temperature_offset: float
    scd40_temp: float
    scd40_humidity: float
    carbon_dioxide: int
    last_update: float

class TresholdValue(TypedDict):
    label: str
    emoji: str

# for example: 600 would be 600 up until 800
CO2_TRESHOLDS: Dict[int, TresholdValue] = {
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

TEMP_TRESHOLDS: Dict[int, TresholdValue] = {
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

HUMIDITY_TRESHOLDS: Dict[int, TresholdValue] = {
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

RESISTANCE_TRESHOLDS: Dict[int, TresholdValue] = {
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

PM25_TRESHOLDS: Dict[int, TresholdValue] = {
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


PM100_TRESHOLDS: Dict[int, TresholdValue] = {
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

OUTDOOR_TEMP_TRESHOLDS: Dict[int, TresholdValue] = {
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

OUTDOOR_HUMIDITY_TRESHOLDS: Dict[int, TresholdValue] = {
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

SUN_POSITION_TRESHOLD: Dict[int, TresholdValue] = {
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

PRESSURE_TRESHOLS: Dict[int, TresholdValue] = {
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
        "emoji":  "🟡"
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

class Climate(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = bot
        self.description = "🌱|Monitor my indoor and outdoor climates"

    def get_ranking(self, current_value: float, tresholds: Dict[int, TresholdValue]) -> TresholdValue:
        """
        Gets the ranking (e.g good, bad, dangerous) for a given value
        """
        found_treshold: TresholdValue = {
            "emoji": "",
            "label": ""
        }

        for value, treshold in sorted(tresholds.items(), key=lambda item: item[0]):
            logger.info(str(current_value) + " " + str(value))
            if current_value < value:
                break

            found_treshold = treshold

        return found_treshold

    def format_embed(self, label: str, unit: str, value: float, treshold: Dict[int, TresholdValue]) -> dict:
        ranking = self.get_ranking(value, treshold)
        return {
            "name": f"{label} {ranking['emoji']}",
            "value": f"{round(value, 2)} {unit} (**{ranking['label']}**)"
        }

    def parse_prometheus_format(self, lines: str) -> dict:
        data = {}
        for line in lines.split("\n"):
            if line.startswith("#"): continue
            if len(line) < 3: continue
            key, value = line.split(" ")

            data[key.strip()] = float(value.strip())

        return data

    def get_sun_angle(self) -> float:
        settings: SettingsType = settings_manager.get_plugin_settings("climate", default_settings)  # type: ignore

        now = datetime.datetime.now()
        hour = now.hour + now.minute / 60 + now.second / 3600
        solar_hour = hour + (settings["longtitude"] - 45) / 15
        nth_day_of_year = (now - datetime.datetime(now.year, 1, 1)).days + 1
        declination = math.radians(23.445 * math.sin(math.radians((360 / 365.25) * (nth_day_of_year - 81))))
        hour_angle = math.radians(15 * (solar_hour - 12))

        result = math.degrees(math.asin(
            math.sin(declination) *
            math.sin(math.radians(settings["latitude"])) +
            math.cos(declination) *
            math.cos(math.radians(settings["latitude"])) *
            math.cos(hour_angle)
        ))

        if result > -1.0:
            refraction = 1.02 / math.tan(math.radians(result + 10.3 / (result + 5.11))) / 60
            result += refraction

        return result

    @commands.command()
    async def indoors(self, ctx: commands.Context):
        res = await requests_async.get("http://192.168.1.45:8080/latest/indoor")
        data: IndoorData = res.json()

        embed = discord.Embed(
            title="Climate data",
            description="Information about my indoor climate"
        )

        calculated_temp: float = data['scd40_temp'] - data['temperature_offset']
        air_humidity: float = (data["scd40_humidity"] + data["relative_humidity"]) / 2

        embed.add_field(**self.format_embed("CO2", "PPM", data['carbon_dioxide'], CO2_TRESHOLDS))
        embed.add_field(**self.format_embed("Temperature", "°C", calculated_temp, TEMP_TRESHOLDS))
        embed.add_field(**self.format_embed("Relative Humidity", "%", air_humidity, HUMIDITY_TRESHOLDS))
        embed.add_field(**self.format_embed("Air Resistance", "Ω", data['air_resistance'], RESISTANCE_TRESHOLDS))

        embed.set_footer(text=f"Last updated: {time.strftime('%H:%M:%S %d/%m/%Y', time.gmtime(data['last_update']))} (UTC)")

        await send_message(ctx, embed=embed)

    @commands.command()
    async def outdoors(self, ctx: commands.Context):
        res = await requests_async.get("http://192.168.32.2:7777/metrics")
        data = self.parse_prometheus_format(res.text)

        indoor_data = await requests_async.get("http://192.168.32.88:7778/data")

        embed = discord.Embed(
            title="Climate data",
            description=f"Information about my outdoor climate"
        )

        pressure = indoor_data.json()["air_pressure"] * math.pow((1 - 119/44330), -5.225) 

        embed.add_field(**self.format_embed("PM2.5", "µg/m³", data["mc2p5"], PM25_TRESHOLDS))
        embed.add_field(**self.format_embed("PM10.0", "µg/m³", data["mc10p0"], PM100_TRESHOLDS))
        embed.add_field(**self.format_embed("Temperature", "°C", data["temp"], OUTDOOR_TEMP_TRESHOLDS))
        embed.add_field(**self.format_embed("Relative Humidity", "%", data["humidity"], OUTDOOR_HUMIDITY_TRESHOLDS))
        embed.add_field(**self.format_embed("Air Pressure", "hPa", pressure, PRESSURE_TRESHOLS))
        embed.add_field(**self.format_embed("Sun angle", "°", self.get_sun_angle(), SUN_POSITION_TRESHOLD))

        await send_message(ctx, embed=embed)

    @requires_admin()
    @commands.command()
    async def set_coords(self, ctx: commands.Context, latitude: float, longtitude: float):
        settings: SettingsType = settings_manager.get_plugin_settings("climate", default_settings) # type: ignore
        settings["latitude"] = latitude
        settings["longtitude"] = longtitude
        settings_manager.set_plugin_setting("climate", settings)

        await send_message(ctx, "Saved coordinates!")

async def setup(bot):
    await bot.add_cog(Climate(bot))
