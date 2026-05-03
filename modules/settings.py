import json
import pathlib
from typing import Literal, Mapping, Any, TypedDict
import logging
import copy

logger = logging.getLogger("goober")

ActivityType = Literal["listening", "playing", "streaming", "competing", "watching"]


class Activity(TypedDict):
    content: str
    type: ActivityType


class MiscBotOptions(TypedDict):
    ping_line: str
    activity: Activity
    positive_gifs: list[str]
    block_profanity: bool


class BotSettings(TypedDict):
    prefix: str
    owner_ids: list[int]
    blacklisted_users: list[int]
    user_training: bool
    allow_show_mem_command: bool
    react_to_messages: bool
    misc: MiscBotOptions
    enabled_cogs: list[str]
    active_memory: str
    active_model: str


class SettingsType(TypedDict):
    bot: BotSettings
    name: str
    auto_update: bool
    disable_checks: bool
    splash_text_loc: str
    cog_settings: dict[str, Mapping[Any, Any]]


class AdminLogEvent(TypedDict):
    messageId: int
    author: int
    target: str | int
    action: Literal["del", "add", "set"]
    change: Literal["owner_ids", "blacklisted_users", "enabled_cogs"]


class Settings:
    def __init__(self) -> None:
        global instance
        instance = self

        self.settings_dir: pathlib.Path = pathlib.Path(__file__).parent.parent / "settings"
        self.path: pathlib.Path = self.settings_dir / "settings.json"
        self.log_path: pathlib.Path = self.settings_dir / "admin_logs.json"

        if not self.path.exists():
            logger.critical(
                f"Missing settings file from {self.path}! Did you forget to copy settings.example.json?"
            )
            raise ValueError("settings.json file does not exist!")

        self.settings: SettingsType
        self.original_settings: SettingsType

        with open(self.path, "r", encoding="utf-8") as f:
            self.__kv_store: dict = json.load(f)

        self.settings = SettingsType(self.__kv_store)  # type: ignore
        self.original_settings = copy.deepcopy(self.settings)

    def reload_settings(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            self.__kv_store: dict = json.load(f)

        self.settings = SettingsType(self.__kv_store)  # type: ignore
        self.original_settings = copy.deepcopy(self.settings)

    def commit(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

        self.original_settings = self.settings

    def discard(self) -> None:
        self.settings = self.original_settings

    def get_plugin_settings(
        self, plugin_name: str, default: Mapping[Any, Any]
    ) -> Mapping[Any, Any]:
        return self.settings["cog_settings"].get(plugin_name, default)

    def set_plugin_setting(
        self, plugin_name: str, new_settings: Mapping[Any, Any]
    ) -> None:
        self.settings["cog_settings"][plugin_name] = new_settings

        self.commit()

    def add_admin_log_event(self, event: AdminLogEvent):
        if not self.log_path.exists():
            logger.warning("Admin log doesn't exist!")
            with open(self.log_path, "w") as f:
                json.dump([], f)

        with open(self.log_path, "r") as f:
            logs: list[AdminLogEvent] = json.load(f)

        logs.append(event)

        with open(self.log_path, "w") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)


instance: Settings = Settings()
