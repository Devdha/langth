"""한국어 단어 빈도 서비스.

국립국어원 빈도 데이터를 기반으로 단어와 문장의 친숙도 점수를 계산합니다.
"""

import json
from pathlib import Path

_frequency_data: dict[str, int] | None = None


def _load_frequency_data() -> dict[str, int]:
    """빈도 데이터 로드 (싱글톤).

    Returns:
        단어별 빈도 점수 딕셔너리
    """
    global _frequency_data
    if _frequency_data is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "korean_frequency_sample.json"
        if data_path.exists():
            with open(data_path, encoding="utf-8") as f:
                _frequency_data = json.load(f)
        else:
            _frequency_data = {}
    return _frequency_data


def get_word_frequency(word: str) -> int:
    """단어의 빈도 점수를 반환합니다 (0-100).

    Args:
        word: 한국어 단어

    Returns:
        빈도 점수 (높을수록 고빈도). 사전에 없으면 50 (중간값).

    Examples:
        >>> get_word_frequency("엄마")
        95
        >>> get_word_frequency("알수없는단어")
        50
    """
    data = _load_frequency_data()
    # 조사 등 제거하고 어근만 검색 (간단 버전)
    for length in range(len(word), 0, -1):
        prefix = word[:length]
        if prefix in data:
            return data[prefix]
    return 50  # 기본값


def get_sentence_frequency_score(sentence: str) -> float:
    """문장의 평균 빈도 점수를 계산합니다.

    Args:
        sentence: 한국어 문장

    Returns:
        평균 빈도 점수 (0-100)

    Examples:
        >>> get_sentence_frequency_score("엄마가 라면 먹어요")
        80.0  # (95 + 75 + 88 + ...) / 4
    """
    words = sentence.split()
    if not words:
        return 50.0

    scores = [get_word_frequency(word) for word in words]
    return sum(scores) / len(scores)
