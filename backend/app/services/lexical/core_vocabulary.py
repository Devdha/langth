"""Core vocabulary helpers for therapy generation."""

from __future__ import annotations

from typing import Iterable


DEFAULT_CORE_WORDS: dict[str, tuple[str, ...]] = {
    "ko": (
        "더",
        "또",
        "아니",
        "네",
        "싫어",
        "줘",
        "이거",
        "저거",
        "뭐",
        "어디",
    ),
    "en": (
        "more",
        "want",
        "no",
        "yes",
        "help",
        "go",
        "stop",
        "my",
        "that",
        "what",
    ),
}


def normalize_core_words(core_words: Iterable[str] | None) -> list[str]:
    if not core_words:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()
    for word in core_words:
        if word is None:
            continue
        cleaned_word = str(word).strip()
        if not cleaned_word:
            continue
        if cleaned_word in seen:
            continue
        seen.add(cleaned_word)
        cleaned.append(cleaned_word)

    return cleaned


def resolve_core_words(language: str, core_words: Iterable[str] | None) -> list[str]:
    lang = language.lower()
    if lang not in DEFAULT_CORE_WORDS:
        raise ValueError(f"Unsupported language for core vocabulary: {language}")

    cleaned = normalize_core_words(core_words)
    if cleaned:
        return cleaned

    return list(DEFAULT_CORE_WORDS[lang])
