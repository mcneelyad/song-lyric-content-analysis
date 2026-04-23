from dotenv import load_dotenv
from functools import lru_cache
import json
import logging
import os
import sys

import lyricsgenius

from schemas.song_schema import LyricsData, Song

load_dotenv()

MAX_SONGS_PER_ARTIST = 25

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_existing_lyrics(genre: str) -> list[dict]:
    path = f"data/raw_lyrics/{genre}.json"
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def load_artists() -> dict[str | str]:
    data = ""
    with open("data/artists.json") as file:
        data = file.read()

    return json.loads(data)

@lru_cache
def build_genius_client() -> lyricsgenius.Genius:
    token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")
    if not token:
        logger.error("Missing genius api access token. Please add it to the .env file")
        sys.exit(1)

    genius = lyricsgenius.Genius(token)

    genius.verbose = False
    genius.remove_section_headers = True  # Remove [Chorus], [Verse], etc.
    genius.excluded_terms = [
        "(Remix)",
        "(Live)",
        "[Mixed]",
        "(Demo)",
        "(Acoustic)",
        "(Radio Edit)",
        "(Clean)",
        "(Explicit)",
    ]
    genius.timeout = 20
    genius.retries = 3

    return genius


def fetch_songs(genius: lyricsgenius.Genius, artist: str) -> list:
    artist_detail = genius.search_artist(
        artist,
        max_songs=MAX_SONGS_PER_ARTIST,
        sort="popularity",
        include_features=False,  # exclude songs where the artist is only featured to avoid massive skipping
    )

    if not artist_detail:
        logger.warning(f'Artist "{artist}" not found, skipping.')
        return []

    songs = getattr(artist_detail, "songs", []) or []
    logger.info(f"{artist} songs found: {len(songs)}")
    return songs


def fetch_lyrics(
    songs: list,
    artist: str,
    genre: str,
    start_id: int = 0,
    existing_keys: set[tuple[str, str]] | None = None,
    max_new: int = MAX_SONGS_PER_ARTIST,
) -> tuple[list[Song], int]:
    if existing_keys is None:
        existing_keys = set()
    results = []
    current_id = start_id
    for song in songs:
        if len(results) >= max_new:
            break
        title = getattr(song, "title", "(unknown title)")
        song_artist = getattr(song, "artist", artist)
        raw_lyrics = getattr(song, "lyrics", None)

        if (song_artist.lower(), title.lower()) in existing_keys:
            logger.info(f'Skipping "{title}" by {song_artist}, already fetched.')
            continue

        if not raw_lyrics:
            logger.warning(f'No lyrics found for "{title}" by {song_artist}, skipping.')
            continue

        words = raw_lyrics.split()
        lyrics_data = LyricsData(
            raw=raw_lyrics.lower(),
            cleaned="",
            word_count=len(words),
            unique_word_count=len(set(w.lower() for w in words)),
        )
        results.append(Song(
            id=current_id,
            title=title,
            artist=song_artist,
            genre=genre,
            lyrics=lyrics_data,
            album=getattr(song, "album", None),
            year=getattr(song, "year", None),
        ))
        current_id += 1
        logger.info(f'Fetched lyrics for "{title}" by {song_artist}.')

    return results, current_id


if __name__ == "__main__":
    genius = build_genius_client()
    genres = load_artists()

    for genre, artist_list in genres.items():
        existing = load_existing_lyrics(genre)
        existing_keys = {(s["artist"].lower(), s["title"].lower()) for s in existing}
        existing_counts: dict[str, int] = {}
        for s in existing:
            key = s["artist"].lower()
            existing_counts[key] = existing_counts.get(key, 0) + 1

        next_id = max((s["id"] for s in existing), default=-1) + 1
        new_songs: list[Song] = []

        for artist in artist_list:
            if not artist:
                logger.error('Artist "%s" not found.', artist)
                sys.exit(2)

            current_count = existing_counts.get(artist.lower(), 0)
            if current_count >= MAX_SONGS_PER_ARTIST:
                logger.info(f'"{artist}" already has {MAX_SONGS_PER_ARTIST} songs, skipping.')
                continue

            remaining = MAX_SONGS_PER_ARTIST - current_count
            logger.info(f'Searching for songs by {artist} ...')

            songs = fetch_songs(genius, artist)
            fetched, next_id = fetch_lyrics(songs, artist, genre, next_id, existing_keys, remaining)
            new_songs.extend(fetched)

        if new_songs:
            all_songs = existing + [song.model_dump() for song in new_songs]
            output_path = f"data/raw_lyrics/{genre}.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_songs, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(new_songs)} new songs for genre '{genre}' to {output_path}.")
        else:
            logger.info(f"No new songs to save for genre '{genre}'.")