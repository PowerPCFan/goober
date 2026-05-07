import logging
from modules.logger import GooberFormatter
import tracemalloc
import os
import time
import traceback
import sys
from typing import Literal, Set, TypedDict
from modules.settings import instance as settings_manager, ActivityType
import discord
from discord.ext import commands
from better_profanity import profanity
import markovify
from modules.markovmemory import load_memory, load_markov_model, save_memory, train_markov_model
from modules.sentenceprocessing import append_mentions_to_18digit_integer, preprocess_message
from modules.unhandledexception import handle_exception, handle_exception_with_context

logger = logging.getLogger("goober")
logger.setLevel(logging.DEBUG)

level_name = settings_manager.settings.bot.log_level.upper()
console_level = logging._nameToLevel.get(level_name, logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(console_level)
console_handler.setFormatter(GooberFormatter())

file_handler = logging.FileHandler("log.txt", mode="w+", encoding="UTF-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(GooberFormatter(colors=False))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.info("Starting...")

messages_recieved = 0

settings = settings_manager.settings

sys.excepthook = handle_exception
tracemalloc.start()


class MessageMetadata(TypedDict):
    user_id: str
    user_name: str
    guild_id: str | Literal["DM"]
    guild_name: str | Literal["DM"]
    channel_id: str
    channel_name: str
    message: str
    timestamp: float


os.makedirs("data", exist_ok=True)

# Constants with type hints
positive_gifs: list[str] = settings.bot.misc.positive_gifs
currenthash: str = ""
launched: bool = False
slash_commands_enabled: bool = False

# Set up Discord bot intents and create bot instance
intents: discord.Intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True
intents.members = True

bot: commands.Bot = commands.Bot(
    command_prefix=settings.bot.prefix,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        everyone=False, roles=False, users=False, replied_user=True
    ),
    help_command=None
)

# Load memory and Markov model for text generation
memory: list[str | dict[Literal["_meta"], MessageMetadata]] = load_memory()
markov_model: markovify.Text | None = load_markov_model()
if not markov_model:
    logger.error('Markov model not found!')
    memory = load_memory()
    markov_model = train_markov_model(memory)


# connect to synchub
# synchub.try_to_connect()

generated_sentences: Set[str] = set()
used_words: Set[str] = set()


async def load_cogs_from_folder(bot: commands.Bot, folder_name: str, internal: bool = False):
    for filename in [file for file in os.listdir(folder_name) if file.endswith(".py")]:
        cog_name: str = filename[:-3]

        if not internal and cog_name not in settings.bot.enabled_cogs:
            logger.debug(f"Skipping cog {cog_name} (not in enabled cogs)")
            continue

        module_path = folder_name.replace("/", ".").replace("\\", ".") + f".{cog_name}"

        try:
            await bot.load_extension(module_path)
            logger.info(f"Loaded cog: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to load cog: {cog_name} {e}")
            traceback.print_exc()


# Event: Called when the bot is ready
@bot.event
async def on_ready() -> None:
    global launched

    if launched:
        return

    await load_cogs_from_folder(bot, "assets/cogs/internal", internal=True)
    await load_cogs_from_folder(bot, "assets/cogs")
    try:
        synced: list[discord.app_commands.AppCommand] = await bot.tree.sync()

        logger.info(f"Synced {len(synced)} commands!")
        logger.info(f"{settings.name} has started! You're the star of the show now baby!")

    except discord.errors.Forbidden as perm_error:
        logger.error(f"Permission error while syncing commands: {perm_error}")
        logger.error(
            "Make sure the bot has the 'applications.commands' scope and is invited with the correct permissions."
        )
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        traceback.print_exc()

    if not settings.bot.misc.activity.content:
        return

    activities: dict[ActivityType, discord.ActivityType] = {
        "listening": discord.ActivityType.listening,
        "playing": discord.ActivityType.playing,
        "streaming": discord.ActivityType.streaming,
        "competing": discord.ActivityType.competing,
        "watching": discord.ActivityType.watching,
    }

    await bot.change_presence(
        activity=discord.Activity(
            type=activities.get(
                settings.bot.misc.activity.type,
                discord.ActivityType.unknown,
            ),
            name=settings.bot.misc.activity.content,
        )
    )
    launched = True

    logger.info(f"Running as {bot.user}")
    logger.info(f"Guilds: {", ".join([guild.name for guild in bot.guilds])}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandInvokeError):
        original: Exception = error.original
        await handle_exception_with_context(
            ctx,
            type(original),
            original,
            original.__traceback__,
            context=f"Command: {ctx.command} | User: {ctx.author}",
        )
    else:
        await handle_exception_with_context(
            ctx,
            type(error),
            error,
            error.__traceback__,
            context=f"Command: {ctx.command} | User: {ctx.author}",
        )


# Event: Called on every message
@bot.event
async def on_message(message: discord.Message) -> None:
    global memory, markov_model, messages_recieved

    messages_recieved += 1

    if message.author.bot:
        return

    if message.author.id in settings.bot.blacklisted_users:
        return

    await bot.process_commands(message)

    if not message.content:
        return

    if not settings.bot.user_training:
        return

    if (
        settings.bot.misc.block_profanity
        and profanity.contains_profanity(message.content)
    ):
        return

    formatted_message: str = append_mentions_to_18digit_integer(message.content)
    cleaned_message: str = preprocess_message(formatted_message)
    if cleaned_message:
        memory.append(cleaned_message)

        message_metadata: MessageMetadata = {
            "user_id": str(message.author.id),
            "user_name": str(message.author),
            "guild_id": str(message.guild.id) if message.guild else "DM",
            "guild_name": str(message.guild.name) if message.guild else "DM",
            "channel_id": str(message.channel.id),
            "channel_name": str(message.channel),
            "message": message.content,
            "timestamp": time.time(),
        }
        try:
            if isinstance(memory, list):
                memory.append({"_meta": message_metadata})
            else:
                logger.warning("Memory is not a list; can't append metadata")
        except Exception as e:
            logger.warning(f"Failed to append metadata to memory: {e}")

        if messages_recieved % 10 == 0:
            logger.info("Saving memory")
            save_memory(memory)

    if len(message.content.strip().split()) < 1:
        logger.info("Skipping positivty checks due to message being too short")
        return


# Event: Called on every interaction (slash command, etc.)
@bot.event
async def on_interaction(interaction: discord.Interaction) -> None:
    logger.info(f"{f'Info: {interaction.user} ran '} {interaction.user.name}")


# Global check: Block blacklisted users from running commands
@bot.check
async def block_blacklisted(ctx: commands.Context) -> bool:
    if ctx.author.id not in settings.bot.blacklisted_users:
        return True

    try:
        if isinstance(ctx, discord.Interaction):
            if not ctx.response.is_done():
                await ctx.response.send_message('blacklisted', ephemeral=True)
            else:
                await ctx.followup.send('blacklisted', ephemeral=True)
        else:
            await ctx.send('Blacklisted user', ephemeral=True)
    except Exception:
        return False

    return True


# Helper: Improve sentence coherence (simple capitalization fix)
def improve_sentence_coherence(sentence: str) -> str:
    # Capitalizes "i" to "I" in the sentence
    sentence = sentence.replace(" i ", " I ")
    return sentence


# Start the bot
if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_BOT_TOKEN", ""))
