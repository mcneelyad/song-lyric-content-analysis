from pydantic import Field
from typing import Optional

from schemas.base_schema import BaseSchema


class DetoxifyScores(BaseSchema):
    toxicity: float = Field(ge=0.0, le=1.0)
    sexual_explicit: float = Field(ge=0.0, le=1.0)
    obscene: float = Field(ge=0.0, le=1.0)
    insult: float = Field(ge=0.0, le=1.0)


class LewdnessScores(BaseSchema):
    explicit_word_density: float
    profanity_score: float
    detoxify: DetoxifyScores
    composite_score: float