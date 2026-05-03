import websocket
from modules.settings import instance as settings_manager
import logging
import threading


logger = logging.getLogger("goober")
settings = settings_manager.settings


class SyncConnector:
    def __init__(self, url: str):
        self.connected: bool = True
        self.url = url
        self.client: websocket.WebSocket | None = None

        self.connection_thread: threading.Thread = threading.Thread(target=self.try_to_connect)
        self.connection_thread.start()

    def __connect(self) -> bool:
        try:
            self.client = websocket.create_connection(self.url, timeout=3)
        except OSError as e:
            logger.debug(e)
            logger.debug(e.strerror)
            return False

        return True

    def try_to_connect(self) -> bool:
        if self.__connect():
            logger.info("Connected to sync hub!")
            self.connected = True
        else:
            logger.error("Failed to connect to sync hub.. Disabling for the time being")
            self.connected = False

        return self.connected

    def get_connected(self, retry_depth: int = 0) -> str:
        if not settings.bot.sync_hub.enabled:
            logger.info("Skipping sync hub check")
            return "not enabled"

        if not self.client:
            logger.error("Client not connected")
            return "not connected"

        if retry_depth > 2:
            return "too many attempts1"

        if not self.connected:
            logger.warning("Not connected to sync hub.. Trying to reconnect")
            if self.try_to_connect():
                logger.info("Succesfully reconnected!")
            else:
                return "reconnect failed"

        try:
            self.client.send(f"event=get;ref=stats;channel=0;name={settings.name}")
            return str(self.client.recv())
        except Exception as e:
            logger.debug(e)
            logger.error("Connection to sync hub reset! Retrying...")

            if not self.__connect():
                logger.error("Failed to reconnect to sync hub... Disabling")
                self.connected = False
                return "reconnection failed"

            logger.info("Managed to reconnect to sync hub! Retrying requests")
            self.connected = True
            return self.get_connected(retry_depth=retry_depth + 1)

    def can_react(self, message_id: int, channel_id: int) -> bool:
        """
        Checks if goober can react to a messsage
        """

        return self.can_event(message_id, channel_id, "react")

    def can_breaking_news(self, message_id: int, channel_id: int) -> bool:
        """
        Checks if goober can send a breaking news alert
        """

        return self.can_event(message_id, channel_id, "breaking_news")

    def can_convert(self, message_id: int, channel_id: int) -> bool:
        if not settings.bot.sync_hub.enabled:
            logger.info("Skipping sync hub check")
            return True

        return self.can_event(message_id, channel_id, "convert")

    def can_event(self, message_id: int, channel_id: int, event: str, retry_depth: int = 0) -> bool:
        """
        Checks if goober can send a breaking news alert
        """

        logger.debug(f"Checking {event} for message {message_id}")

        if not settings.bot.sync_hub.enabled:
            logger.info("Skipping sync hub check")
            return True

        if retry_depth > 2:
            logger.error("Too many retries. Returning false")
            return False

        if not self.client:
            logger.error("Client not connected")
            return False

        if not self.connected:
            logger.warning("Not connected to sync hub.. Trying to reconnect")
            if self.try_to_connect():
                logger.info("Succesfully reconnected!")
            else:
                return False

        try:
            self.client.send(f"event={event};ref={message_id};channel={channel_id};name={settings.name}")
            return self.client.recv() == "unhandled"
        except Exception as e:
            logger.debug(e)
            logger.error("Connection to sync hub reset! Retrying...")

            if not self.__connect():
                logger.error("Failed to reconnect to sync hub... Disabling")
                self.connected = False
                return False

            logger.info("Managed to reconnect to sync hub! Retrying requests")
            self.connected = True
            return self.can_event(message_id, channel_id, event, retry_depth + 1)


instance = SyncConnector(settings.bot.sync_hub.url)
