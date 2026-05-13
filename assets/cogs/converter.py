# fmt: off
# ruff: noqa: E501

import logging
import random
import re
from copy import copy
from typing import TYPE_CHECKING, Any, TypedDict

import discord
from discord.ext import commands

from modules.embeds import send_error, send_success, send_warning
from modules.permission import requires_admin
from modules.settings import instance as settings_manager
from modules.sync_connector import instance as synchub

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

logger = logging.getLogger("goober")
settings = settings_manager.settings


class SettingsType(TypedDict):
    blacklisted_words: list[str]


default_settings: SettingsType = { "blacklisted_words": [] }


class Unit(TypedDict):
    shorthand: str
    name: str


class Conversion(TypedDict):
    value: float
    unit: str


class ConvertedValue(TypedDict):
    metric: Conversion | Any
    imperial: Conversion | Any


Fahrenheit: Unit = {
    "name": "Fahrenheit",
    "shorthand": " °F",
}

Celsius: Unit = {
    "name": "Celsius",
    "shorthand": " °C",
}

Feet: Unit = {
    "name": "Feet",
    "shorthand": " ft",
}

Meters: Unit = {
    "name": "Meter",
    "shorthand": " m",
}

Inch: Unit = {
    "name": "Inch",
    "shorthand": '"',
}

Centimeter: Unit = {
    "name": "Centimeter",
    "shorthand": " cm",
}

Mile: Unit = {
    "name": "Mile",
    "shorthand": " mile(s)",
}

Kilometer: Unit = {
    "name": "Kilometer",
    "shorthand": "km",
}

Liters: Unit = {
    "name": "Liter",
    "shorthand": " L",
}

Gallons: Unit = {
    "name": "Gallon",
    "shorthand": " gal",
}

Kilogram: Unit = {
    "name": "Kilogram",
    "shorthand": " kg",
}

Pounds: Unit = {
    "name": "Pound",
    "shorthand": " lbs",
}

Grams: Unit = {
    "name": "Gram",
    "shorthand": " g",
}

Ounces: Unit = {
    "name": "Ounce",
    "shorthand": " oz",
}


Reactions = [
    "That's {val} btw",
    "you could have just said {val} heh",
    "That's {val} just in case you wanted to know",
    "that's {val} since you don't know how to Google...",
    "since your internet is down that's {val}",
    "That's {val}",
]


def to_speed_unit(unit: Unit) -> Unit:
    unit = copy(unit)

    unit["name"] += " per hour"

    if unit["shorthand"] == Mile["shorthand"]:
        unit["shorthand"] = "mph"
    else:
        unit["shorthand"] += "/h"

    return unit


class Converters:
    @staticmethod
    def from_celsius(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "unit": Fahrenheit,
                "value": (value * 1.8) + 32,
            },
        }

    @staticmethod
    def from_fahrenheit(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Celsius,
                "value": (value - 32) / 1.8,
            },
            "imperial": None,
        }

    @staticmethod
    def from_meters(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "unit": Feet,
                "value": value * 3.28084,
            },
        }

    @staticmethod
    def from_feet(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Meters,
                "value": value * 0.3048,
            },
            "imperial": None,
        }

    @staticmethod
    def from_centimeters(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "unit": Inch,
                "value": value / 2.54,
            },
        }

    @staticmethod
    def from_inches(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Centimeter,
                "value": value * 2.54,
            },
            "imperial": {
                "unit": Feet,
                "value": value * 0.0833333333,
            },
        }

    @staticmethod
    def from_kilometers(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "unit": Mile,
                "value": value * 0.621371192,
            },
        }

    @staticmethod
    def from_miles(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Kilometer,
                "value": value / 0.621371192,
            },
            "imperial": None,
        }

    @staticmethod
    def from_kmh(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "value": Converters.from_kilometers(value)["imperial"]["value"],
                "unit": to_speed_unit(Mile),
            },
        }

    @staticmethod
    def from_mph(value: float) -> ConvertedValue:
        return {
            "metric": {
                "value": Converters.from_miles(value)["metric"]["value"],
                "unit": to_speed_unit(Kilometer),
            },
            "imperial": None,
        }

    @staticmethod
    def from_ms(value: float) -> ConvertedValue:
        return {
            "metric": {
                "value": value * 3.6,
                "unit": to_speed_unit(Kilometer),
            },
            "imperial": {
                "unit": to_speed_unit(Mile),
                "value": value * 2.23693629,
            },
        }

    @staticmethod
    def from_gallons(value: float) -> ConvertedValue:
        return {
            "metric": {
                "value": value * 3.78541178,
                "unit": Liters,
            },
            "imperial": None,
        }

    @staticmethod
    def from_liters(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "value": value * 0.264172052,
                "unit": Gallons,
            },
        }

    @staticmethod
    def from_kilograms(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "value": value * 2.20462262,
                "unit": Pounds,
            },
        }

    @staticmethod
    def from_pounds(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Kilogram,
                "value": value * 0.45359237,
            },
            "imperial": None,
        }

    @staticmethod
    def from_grams(value: float) -> ConvertedValue:
        return {
            "metric": None,
            "imperial": {
                "unit": Ounces,
                "value": value * 0.0352739619,
            },
        }

    @staticmethod
    def from_ounces(value: float) -> ConvertedValue:
        return {
            "metric": {
                "unit": Grams,
                "value": value * 28.349523125,
            },
            "imperial": None,
        }


class Converter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "🔄|Automatically convert between units (Metric/Imperial) found in chats"
        self.regexes: dict[re.Pattern, Callable] = {
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(c|\*c)(\s|$)", re.IGNORECASE): Converters.from_celsius,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(f|\*f)(\s|$)", re.IGNORECASE): Converters.from_fahrenheit,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(m|meters)(\s|$)", re.IGNORECASE): Converters.from_meters,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(cm|centimeter|centimeters)(\s|$)", re.IGNORECASE): Converters.from_centimeters,
            re.compile(r'(?:\s|^)(-?[0-9(.?|,?)]+)\s?("|in|inches)(\s|$)', re.IGNORECASE): Converters.from_inches,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(mi\.|mi|miles|mile)(\s|$)", re.IGNORECASE): Converters.from_miles,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(km|kilometers|kilometer)(\s|$)", re.IGNORECASE): Converters.from_kilometers,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(km\/h|kmh|kph)(\s|$)", re.IGNORECASE): Converters.from_kmh,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(miles\/h|mph)(\s|$)", re.IGNORECASE): Converters.from_mph,
            re.compile(r"""(-?[0-9(.?|,?)]+)\s?(')(-?[0-9(.?|,?)]+)?("?)(\s|$)""", re.IGNORECASE): Converters.from_feet,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(m\/s)(\s|$)", re.IGNORECASE): Converters.from_ms,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(gal|gallons|gallon)(\s|$)", re.IGNORECASE): Converters.from_gallons,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(l|liter|liters)(\s|$)", re.IGNORECASE): Converters.from_liters,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(kg|kilos|kilo|kilograms|kilogram)(\s|$)", re.IGNORECASE): Converters.from_kilograms,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(pounds|lbs|lb)(\s|$)", re.IGNORECASE): Converters.from_pounds,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(grams|gram|g)(\s|$)"): Converters.from_grams,
            re.compile(r"(?:\s|^)(-?[0-9(.?|,?)]+)\s?(oz|ounce|ounces)(\s|$)", re.IGNORECASE): Converters.from_ounces,
        }

    def __format_response(self, converted_values: list[ConvertedValue]) -> str:
        logger.debug(f"Values: {converted_values}")
        message: str = ""

        for i, converted in enumerate(converted_values):
            temp_line: str = ", and " if (i == len(converted_values) - 1 and i != 0) else ", " if i != 0 else ""
            data_line: str = ""

            for data in converted.values():
                if data is None:
                    continue

                value = data["value"]  # pyright: ignore[reportIndexIssue]
                shorthand = data["unit"]["shorthand"]  # pyright: ignore[reportIndexIssue]

                data_line += f"{' or ' if data_line else ''}**{round(value, 2)}{shorthand}**"
                logger.debug(temp_line)

            temp_line += data_line
            message += temp_line

        return f"-# {random.choice(Reactions).format(val=message)}"  # noqa: S311

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        settings: SettingsType = settings_manager.get_plugin_settings("converter", default_settings)  # type: ignore[assignment]

        if message.author.bot:
            return

        found_units_dict: dict[int, ConvertedValue] = {}

        for regex, conversion_func in self.regexes.items():
            matches: Iterator[re.Match] | None = regex.finditer(message.content)

            if not matches:
                continue

            for match in matches:
                match_string: str = "".join(match.groups()).strip()
                logger.debug(match.groups())
                if match_string in settings.get("blacklisted_words"):
                    logger.info(f"Skipping match {match_string} due to it being blacklisted")
                    continue

                value: ConvertedValue | None = None

                if conversion_func == Converters.from_feet:
                    value = conversion_func(
                        float(match.groups()[0].replace(",", "."))
                        + Converters.from_inches(float(match.groups()[2].replace(",", ".")))["imperial"]["value"],
                    )
                else:
                    value = conversion_func(float(match.groups()[0].replace(",", ".")))

                if value is not None:
                    found_units_dict[match.start()] = value

        unit_list: list[tuple[int, ConvertedValue]] = list(found_units_dict.items())
        sorted_units = [val[1] for val in sorted(unit_list, key=lambda val: val[0])]

        if len(sorted_units) > 0:
            # check for synchub down here so it only checks if the regex matches
            if not synchub.can_convert(message.id, message.channel.id):
                return
            await message.reply(self.__format_response(sorted_units))

    @requires_admin()
    @commands.hybrid_command(description="Blacklist a word from automatic conversion")
    async def blacklist_word(self, ctx: commands.Context, word: str | None) -> None:
        settings: SettingsType = settings_manager.get_plugin_settings("converter", default_settings)  # type: ignore[assignment]

        if not word:
            await send_error(ctx, title="No Word Specified", description="Please specify a word.")
            return

        if word in settings["blacklisted_words"]:
            await send_warning(ctx, title="Word Already Blacklisted", description=f"`{word}` is already blacklisted.")
            return

        settings["blacklisted_words"].append(word or "")

        settings_manager.set_plugin_setting("converter", settings)
        await send_success(ctx, title="Word Blacklisted", description=f"Successfully blacklisted `{word}`.")

    @requires_admin()
    @commands.hybrid_command(description="Whitelist a blacklisted word for automatic conversion")
    async def whitelist_word(self, ctx: commands.Context, word: str | None) -> None:
        settings: SettingsType = settings_manager.get_plugin_settings("converter", default_settings)  # type: ignore[assignment]

        if not word:
            await send_error(ctx, title="No Word Specified", description="Please specify a word.")
            return

        if word not in settings["blacklisted_words"]:
            await send_warning(ctx, title="Word Not Blacklisted", description=f"`{word}` is not currently blacklisted.")
            return

        settings["blacklisted_words"].remove(word)

        settings_manager.set_plugin_setting("converter", settings)
        await send_success(ctx, title="Word Whitelisted", description=f"Successfully whitelisted `{word}`.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Converter(bot))
