import os
import platform
from typing import Callable, List
from dotenv import load_dotenv
import pathlib

env_path = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

available_cogs: Callable[[], List[str]] = lambda: [
    file[:-3] for file in os.listdir("assets/cogs") if file.endswith(".py")
]

ANSI = "\033["
RED = f"{ANSI}31m"
GREEN = f"{ANSI}32m"
YELLOW = f"{ANSI}33m"
PURPLE = f"{ANSI}35m"
DEBUG = f"{ANSI}90m"
RESET = f"{ANSI}0m"

VERSION_URL = "https://raw.githubusercontent.com/gooberinc/version/main"
UPDATE_URL = VERSION_URL + "/latest_version.json"
print(UPDATE_URL)
LOCAL_VERSION_FILE = "current_version.txt"

arch = platform.machine()
launched = False

local_version = "2.5.0b"
beta = False
