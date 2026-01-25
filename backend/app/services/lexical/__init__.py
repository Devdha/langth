"""Lexical scoring service for Korean child vocabulary."""

from .scorer import (
    get_word_frequency,
    get_age_appropriateness,
    score_sentence_lexical,
)
from .vocabulary import (
    VOCABULARY_BY_AGE,
    WORD_FREQUENCY,
    get_word_age_level,
)

__all__ = [
    "get_word_frequency",
    "get_age_appropriateness",
    "score_sentence_lexical",
    "VOCABULARY_BY_AGE",
    "WORD_FREQUENCY",
    "get_word_age_level",
]
