from .korean import (
    decompose_hangul,
    has_phoneme_at_position,
    find_phoneme_matches,
    PhonemeMatchResult,
    PhonemePosition,
)
from .english import (
    get_phonemes,
    has_target_phoneme,
    find_phoneme_matches_en,
    PhonemeMatchResultEn,
    PHONEME_MAP,
)

__all__ = [
    # Korean
    "decompose_hangul",
    "has_phoneme_at_position",
    "find_phoneme_matches",
    "PhonemeMatchResult",
    "PhonemePosition",
    # English
    "get_phonemes",
    "has_target_phoneme",
    "find_phoneme_matches_en",
    "PhonemeMatchResultEn",
    "PHONEME_MAP",
]
