"""Korean phonological rules validator.

This module provides functions to detect various Korean phonological rules:
- Nasalization (비음화): Plain obstruents become nasals before nasals
- Fortition (경음화): Plain consonants become fortis (tense)
- Liaison (연음): Final consonant moves to following onset
- Liquidization (유음화): /n/ becomes /l/ or /l/ becomes /n/
"""

from typing import Literal

import hgtk

# Consonant categories for phonological rules
PLAIN_OBSTRUENTS = {"ㄱ", "ㄷ", "ㅂ"}  # 평폐쇄음
NASALS = {"ㄴ", "ㅁ", "ㅇ"}  # 비음
PLAIN_CONSONANTS = {"ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ"}  # 평음
FORTIS_CONSONANTS = {"ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"}  # 경음
LIQUIDS = {"ㄹ"}  # 유음

# Mapping for nasalization: plain obstruent -> nasal
NASALIZATION_MAP = {
    "ㄱ": "ㅇ",  # [k] -> [ŋ]
    "ㄷ": "ㄴ",  # [t] -> [n]
    "ㅂ": "ㅁ",  # [p] -> [m]
}

# Mapping for fortition: plain -> fortis
FORTITION_MAP = {
    "ㄱ": "ㄲ",
    "ㄷ": "ㄸ",
    "ㅂ": "ㅃ",
    "ㅅ": "ㅆ",
    "ㅈ": "ㅉ",
}

# Final consonants that can trigger fortition
FORTITION_TRIGGERS = {"ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ", "ㄳ", "ㄵ", "ㄶ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅄ"}


def decompose_char(char: str) -> tuple[str, str, str] | None:
    """Decompose a Korean syllable into onset, nucleus, coda.

    Args:
        char: A single Korean character.

    Returns:
        Tuple of (onset, nucleus, coda) or None if not a Korean syllable.
        Coda is empty string if there's no final consonant.
    """
    try:
        cho, jung, jong = hgtk.letter.decompose(char)
        return (cho, jung, jong if jong else "")
    except Exception:
        return None


def is_hangul_syllable(char: str) -> bool:
    """Check if a character is a complete Korean syllable."""
    return decompose_char(char) is not None


def get_syllables(text: str) -> list[tuple[int, str, tuple[str, str, str]]]:
    """Extract Korean syllables with their positions and decompositions.

    Args:
        text: Input text.

    Returns:
        List of (index, character, (onset, nucleus, coda)) tuples.
    """
    result = []
    for i, char in enumerate(text):
        decomposed = decompose_char(char)
        if decomposed is not None:
            result.append((i, char, decomposed))
    return result


def detect_nasalization(text: str) -> list[tuple[int, str]]:
    """Detect nasalization environments in the text.

    Nasalization occurs when a plain obstruent (ㄱ, ㄷ, ㅂ) in coda position
    precedes a nasal consonant (ㄴ, ㅁ) in onset position of the next syllable.

    Example: 국물 [궁물], 밥먹다 [밤먹따]

    Args:
        text: Input Korean text.

    Returns:
        List of (position, description) tuples where nasalization occurs.
    """
    syllables = get_syllables(text)
    results = []

    for i in range(len(syllables) - 1):
        pos1, char1, (_, _, coda) = syllables[i]
        pos2, char2, (onset2, _, _) = syllables[i + 1]

        # Check if coda is a plain obstruent and next onset is a nasal
        if coda in PLAIN_OBSTRUENTS and onset2 in {"ㄴ", "ㅁ"}:
            nasalized = NASALIZATION_MAP.get(coda, coda)
            description = f"{char1}{char2}: {coda} -> {nasalized} (before {onset2})"
            results.append((pos1, description))

    return results


def detect_fortition(text: str) -> list[tuple[int, str]]:
    """Detect fortition (tensification) environments in the text.

    Fortition occurs when a plain consonant (ㄱ, ㄷ, ㅂ, ㅅ, ㅈ) in onset position
    follows a syllable with an obstruent coda.

    Example: 학교 [학꾜], 국밥 [국빱]

    Args:
        text: Input Korean text.

    Returns:
        List of (position, description) tuples where fortition occurs.
    """
    syllables = get_syllables(text)
    results = []

    for i in range(len(syllables) - 1):
        pos1, char1, (_, _, coda) = syllables[i]
        pos2, char2, (onset2, _, _) = syllables[i + 1]

        # Check if coda triggers fortition and next onset is a plain consonant
        # Simple coda check (ignoring complex codas for now)
        if coda in {"ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ"} and onset2 in PLAIN_CONSONANTS:
            fortified = FORTITION_MAP.get(onset2, onset2)
            description = f"{char1}{char2}: {onset2} -> {fortified} (after coda {coda})"
            results.append((pos2, description))

    return results


def detect_liaison(text: str) -> list[tuple[int, str]]:
    """Detect liaison (resyllabification) environments in the text.

    Liaison occurs when a syllable with a coda is followed by a syllable
    starting with the null onset (ㅇ). The coda moves to become the onset.

    Example: 음악 [으막], 연인 [여닌]

    Args:
        text: Input Korean text.

    Returns:
        List of (position, description) tuples where liaison occurs.
    """
    syllables = get_syllables(text)
    results = []

    for i in range(len(syllables) - 1):
        pos1, char1, (_, _, coda) = syllables[i]
        pos2, char2, (onset2, _, _) = syllables[i + 1]

        # Check if coda exists and next onset is null (ㅇ)
        if coda and coda != "" and onset2 == "ㅇ":
            description = f"{char1}{char2}: coda {coda} -> onset of next syllable"
            results.append((pos1, description))

    return results


def detect_liquidization(text: str) -> list[tuple[int, str]]:
    """Detect liquidization environments in the text.

    Liquidization occurs in two cases:
    1. ㄴ -> ㄹ when adjacent to ㄹ (e.g., 신라 [실라])
    2. ㄹ -> ㄴ in certain environments (less common)

    Example: 신라 [실라], 난로 [날로]

    Args:
        text: Input Korean text.

    Returns:
        List of (position, description) tuples where liquidization occurs.
    """
    syllables = get_syllables(text)
    results = []

    for i in range(len(syllables) - 1):
        pos1, char1, (_, _, coda) = syllables[i]
        pos2, char2, (onset2, _, _) = syllables[i + 1]

        # Case 1: coda ㄴ + onset ㄹ -> ㄹㄹ (신라 -> 실라)
        if coda == "ㄴ" and onset2 == "ㄹ":
            description = f"{char1}{char2}: ㄴ -> ㄹ (before ㄹ)"
            results.append((pos1, description))

        # Case 2: coda ㄹ + onset ㄴ -> ㄹㄹ (난로 -> 날로, but typically 설날 -> 설랄)
        elif coda == "ㄹ" and onset2 == "ㄴ":
            description = f"{char1}{char2}: ㄴ -> ㄹ (after ㄹ)"
            results.append((pos2, description))

    return results


RuleMode = Literal["avoid", "require"]


def check_phonological_rules(text: str, mode: RuleMode = "avoid") -> tuple[bool, list[str]]:
    """Check if text meets phonological rule requirements.

    This function checks for all phonological rule environments and returns
    whether the text passes based on the mode.

    Args:
        text: Input Korean text to analyze.
        mode: How to handle rule environments.
            - "avoid": Return False if any rule environment is found (useful for
                       generating text that avoids complex pronunciation).
            - "require": Return False if no rule environment is found (useful for
                         generating text that practices specific rules).

    Returns:
        Tuple of (passed, messages) where:
            - passed: True if text meets the mode requirements, False otherwise.
            - messages: List of descriptions of found rule environments.

    Examples:
        >>> check_phonological_rules("학교", "avoid")
        (False, ["Fortition: 학교: ㄱ -> ㄲ (after coda ㄱ)"])

        >>> check_phonological_rules("사과", "avoid")
        (True, [])
    """
    messages = []

    # Detect all rule environments
    nasalizations = detect_nasalization(text)
    for pos, desc in nasalizations:
        messages.append(f"Nasalization: {desc}")

    fortitions = detect_fortition(text)
    for pos, desc in fortitions:
        messages.append(f"Fortition: {desc}")

    liaisons = detect_liaison(text)
    for pos, desc in liaisons:
        messages.append(f"Liaison: {desc}")

    liquidizations = detect_liquidization(text)
    for pos, desc in liquidizations:
        messages.append(f"Liquidization: {desc}")

    has_rules = len(messages) > 0

    if mode == "avoid":
        # Pass if no rule environments found
        return (not has_rules, messages)
    else:  # mode == "require"
        # Pass if at least one rule environment found
        return (has_rules, messages)
