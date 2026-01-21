from dataclasses import dataclass
from typing import Literal

import hgtk

PhonemePosition = Literal["onset", "nucleus", "coda", "any"]


@dataclass
class PhonemeMatchResult:
    """음소 매칭 결과를 담는 데이터 클래스.

    Attributes:
        matched_words: 타깃 음소가 포함된 단어 목록
        count: 매칭된 단어 수
        meets_minimum: 최소 출현 횟수 충족 여부
    """
    matched_words: list[str]
    count: int
    meets_minimum: bool = True


def decompose_hangul(char: str) -> tuple[str, str, str] | None:
    """한글 음절을 초성, 중성, 종성으로 분해합니다.

    Args:
        char: 분해할 단일 한글 문자

    Returns:
        (초성, 중성, 종성) 튜플. 종성이 없으면 빈 문자열.
        한글이 아닌 경우 None 반환.

    Examples:
        >>> decompose_hangul("가")
        ("ㄱ", "ㅏ", "")
        >>> decompose_hangul("강")
        ("ㄱ", "ㅏ", "ㅇ")
    """
    try:
        cho, jung, jong = hgtk.letter.decompose(char)
        return (cho, jung, jong if jong else "")
    except Exception:
        return None


def has_phoneme_at_position(
    word: str,
    phoneme: str,
    position: PhonemePosition,
) -> bool:
    """단어에서 특정 위치에 타깃 음소가 있는지 확인합니다.

    Args:
        word: 검사할 단어
        phoneme: 타깃 음소 (예: "ㄹ", "ㅏ")
        position: 검사할 위치
            - "onset": 초성
            - "nucleus": 중성 (모음)
            - "coda": 종성
            - "any": 모든 위치

    Returns:
        해당 위치에 음소가 있으면 True, 없으면 False

    Note:
        초성 'ㅇ'은 무음이므로 타깃에서 제외됩니다.
        종성 'ㅇ'([ŋ])만 유효한 타깃입니다.
    """
    for char in word:
        decomposed = decompose_hangul(char)
        if decomposed is None:
            continue
        cho, jung, jong = decomposed

        # 초성 'ㅇ'은 무음이므로 타깃에서 제외
        if phoneme == "ㅇ":
            if position == "onset":
                return False
            if position == "coda" and jong == "ㅇ":
                return True
            if position == "any" and jong == "ㅇ":
                return True
            continue

        if position == "onset" and cho == phoneme:
            return True
        if position == "nucleus" and jung == phoneme:
            return True
        if position == "coda" and jong == phoneme:
            return True
        if position == "any" and phoneme in (cho, jung, jong):
            return True

    return False


def find_phoneme_matches(
    sentence: str,
    phoneme: str,
    position: PhonemePosition,
    min_occurrences: int = 1,
) -> PhonemeMatchResult:
    """문장에서 타깃 음소를 포함하는 단어들을 찾습니다.

    Args:
        sentence: 검사할 문장
        phoneme: 타깃 음소 (예: "ㄹ")
        position: 검사할 위치 ("onset", "nucleus", "coda", "any")
        min_occurrences: 최소 출현 횟수 (기본값: 1)

    Returns:
        PhonemeMatchResult 객체
            - matched_words: 매칭된 단어 목록
            - count: 매칭된 단어 수
            - meets_minimum: 최소 횟수 충족 여부

    Examples:
        >>> find_phoneme_matches("라면 먹고 싶어요", "ㄹ", "onset")
        PhonemeMatchResult(matched_words=["라면"], count=1, meets_minimum=True)
    """
    words = sentence.split()
    matched_words = []
    for word in words:
        if has_phoneme_at_position(word, phoneme, position):
            matched_words.append(word)
    return PhonemeMatchResult(
        matched_words=matched_words,
        count=len(matched_words),
        meets_minimum=len(matched_words) >= min_occurrences,
    )
