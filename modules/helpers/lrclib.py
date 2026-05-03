from slugify import slugify
from typing import TypedDict, List
import requests_async
import logging


logger = logging.getLogger("goober")


class LRCLIBResponse(TypedDict):
    id: int
    name: str
    trackName: str
    artistName: str
    albumName: str
    duration: float
    instrumental: bool
    plainLyrics: str
    syncedLyrics: str


class LRCLIBFetchError(TypedDict):
    statusCode: int
    name: str
    message: str


class LRCAPI:
    @staticmethod
    async def search_song(search_string: str) -> List[LRCLIBResponse]:
        logger.info("Searching for song lyrics...")
        response = await requests_async.get(f"https://lrclib.net/api/search?q={slugify(search_string, separator='+')}")
        matches: List[LRCLIBResponse] = response.json()

        return matches

    @staticmethod
    async def fetch_song(
        track_name: str,
        artist_name: str,
        album_name: str,
        duration_seconds: float
    ) -> LRCLIBFetchError | LRCLIBResponse:
        logger.info("Fetching song lyrics..")
        response = await requests_async.get("https://lrclib.net/api/get", params={
            "track_name": slugify(track_name, separator='+'),
            "artist_name": slugify(artist_name, separator='+'),
            "album_name": slugify(album_name, separator='+'),
            "duration": round(duration_seconds),
        })
        logger.info(response.url)
        match: LRCLIBFetchError | LRCLIBResponse = response.json()

        return match
