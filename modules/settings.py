import json
import pathlib
from dataclasses import dataclass, asdict
from typing import Literal, Mapping, Any
import logging
import copy

logger = logging.getLogger("goober")

ActivityType = Literal["listening", "playing", "streaming", "competing", "watching"]


@dataclass
class Activity:
    content: str
    type: ActivityType


@dataclass
class MiscBotOptions:
    ping_line: str
    activity: Activity
    positive_gifs: list[str]
    block_profanity: bool


@dataclass
class BotSettings:
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


@dataclass
class SettingsType:
    bot: BotSettings
    name: str
    splash_text_loc: str
    cog_settings: dict[str, Mapping[Any, Any]]


@dataclass
class AdminLogEvent:
    messageId: int
    author: int
    target: str | int
    action: Literal["del", "add", "set"]
    change: Literal["owner_ids", "blacklisted_users", "enabled_cogs"]


def _build_settings(data: Mapping[str, Any]) -> SettingsType:
    bot_data = data["bot"]
    misc_data = bot_data["misc"]

    bot = BotSettings(
        prefix=str(bot_data["prefix"]),
        owner_ids=list(bot_data["owner_ids"]),
        blacklisted_users=list(bot_data["blacklisted_users"]),
        user_training=bool(bot_data["user_training"]),
        allow_show_mem_command=bool(bot_data["allow_show_mem_command"]),
        react_to_messages=bool(bot_data["react_to_messages"]),
        misc=MiscBotOptions(
            ping_line=str(misc_data["ping_line"]),
            activity=Activity(**misc_data["activity"]),
            positive_gifs=list(misc_data["positive_gifs"]),
            block_profanity=bool(misc_data["block_profanity"]),
        ),
        enabled_cogs=list(bot_data["enabled_cogs"]),
        active_memory=str(bot_data["active_memory"]),
        active_model=str(bot_data["active_model"]),
    )

    return SettingsType(
        bot=bot,
        name=str(data["name"]),
        splash_text_loc=str(data["splash_text_loc"]),
        cog_settings=dict(data.get("cog_settings", {})),
    )


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

        self.settings = _build_settings(self.__kv_store)
        self.original_settings = copy.deepcopy(self.settings)

    def reload_settings(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            self.__kv_store: dict = json.load(f)

        self.settings = _build_settings(self.__kv_store)
        self.original_settings = copy.deepcopy(self.settings)

    def commit(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, ensure_ascii=False, indent=4)

        self.original_settings = self.settings

    def discard(self) -> None:
        self.settings = self.original_settings

    def get_plugin_settings(
        self, plugin_name: str, default: Mapping[Any, Any]
    ) -> Mapping[Any, Any]:
        return self.settings.cog_settings.get(plugin_name, default)

    def set_plugin_setting(
        self, plugin_name: str, new_settings: Mapping[Any, Any]
    ) -> None:
        self.settings.cog_settings[plugin_name] = new_settings

        self.commit()

    def add_admin_log_event(self, event: AdminLogEvent | Mapping[str, Any]):
        if not self.log_path.exists():
            logger.warning("Admin log doesn't exist!")
            with open(self.log_path, "w") as f:
                json.dump([], f)

        with open(self.log_path, "r") as f:
            logs: list[dict[str, Any]] = json.load(f)

        if isinstance(event, AdminLogEvent):
            logs.append(asdict(event))
        else:
            logs.append(dict(event))

        with open(self.log_path, "w") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)


instance: Settings = Settings()
