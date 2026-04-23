from typing import Optional

from schemas.base_schema import BaseSchema
from schemas.score_schema import LewdnessScores


class LyricsData(BaseSchema):
    raw: str
    cleaned: str
    word_count: int
    unique_word_count: int


class Song(BaseSchema):
    id: int
    title: str
    artist: str
    genre: str
    lyrics: LyricsData
    scores: Optional[LewdnessScores] = None
    album: Optional[dict] = None
    year: Optional[int] = None
    explicit_flag: bool = False
    source: str = "genius"