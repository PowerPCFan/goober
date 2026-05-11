import pathlib

from dotenv import load_dotenv

load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")

available_cogs: list[str] = [file.stem for file in pathlib.Path("assets/cogs").glob("*.py")]

ANSI = "\033["
RED = f"{ANSI}31m"
GREEN = f"{ANSI}32m"
YELLOW = f"{ANSI}33m"
PURPLE = f"{ANSI}35m"
DEBUG = f"{ANSI}90m"
RESET = f"{ANSI}0m"

launched = False
