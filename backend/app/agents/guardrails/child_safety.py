"""아동 안전 필터.

금칙어를 포함한 문장을 필터링합니다.
"""

import json
from pathlib import Path

_forbidden_words: set[str] | None = None


def _load_forbidden_words() -> set[str]:
    """금칙어 로드 (싱글톤).

    Returns:
        금칙어 집합
    """
    global _forbidden_words
    if _forbidden_words is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "forbidden_words.json"
        if data_path.exists():
            with open(data_path, encoding="utf-8") as f:
                data = json.load(f)
                _forbidden_words = set(data.get("forbidden", []))
        else:
            _forbidden_words = set()
    return _forbidden_words


def is_safe_sentence(sentence: str) -> bool:
    """문장이 아동에게 안전한지 확인합니다.

    Args:
        sentence: 검사할 문장

    Returns:
        안전하면 True, 금칙어 포함 시 False

    Examples:
        >>> is_safe_sentence("라면이 맛있어요")
        True
        >>> is_safe_sentence("술을 마시고 싶어")
        False
    """
    forbidden = _load_forbidden_words()

    sentence_lower = sentence.lower()
    for word in forbidden:
        if word in sentence_lower:
            return False

    return True


def filter_unsafe_sentences(sentences: list[str]) -> list[str]:
    """안전하지 않은 문장을 필터링합니다.

    Args:
        sentences: 검사할 문장 리스트

    Returns:
        안전한 문장만 포함된 리스트

    Examples:
        >>> sentences = ["라면이 맛있어요", "술을 마시고 싶어"]
        >>> filter_unsafe_sentences(sentences)
        ['라면이 맛있어요']
    """
    return [s for s in sentences if is_safe_sentence(s)]
