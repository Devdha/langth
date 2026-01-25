"""영어 음소 탐지 서비스.

CMUdict 기반으로 영어 단어의 발음을 분석하고,
타깃 음소 포함 여부를 확인합니다.
"""
from dataclasses import dataclass
import re

import pronouncing
import g2p_en

# G2P 모델 (싱글톤)
_g2p = None


def _get_g2p():
    """G2P 모델을 지연 로드합니다."""
    global _g2p
    if _g2p is None:
        _g2p = g2p_en.G2p()
    return _g2p


# ARPAbet 음소 매핑 (UI용 설명)
PHONEME_MAP = {
    "R": {"ipa": "/r/", "examples": "red, car, run"},
    "L": {"ipa": "/l/", "examples": "light, ball, let"},
    "S": {"ipa": "/s/", "examples": "sun, bus, sit"},
    "Z": {"ipa": "/z/", "examples": "zoo, nose, zip"},
    "TH": {"ipa": "/θ/", "examples": "think, bath, three"},
    "DH": {"ipa": "/ð/", "examples": "this, mother, the"},
    "SH": {"ipa": "/ʃ/", "examples": "ship, fish, she"},
    "CH": {"ipa": "/tʃ/", "examples": "chip, watch, chair"},
    "F": {"ipa": "/f/", "examples": "fish, leaf, fun"},
    "V": {"ipa": "/v/", "examples": "van, love, very"},
    "K": {"ipa": "/k/", "examples": "cat, back, key"},
    "G": {"ipa": "/g/", "examples": "go, big, get"},
    "T": {"ipa": "/t/", "examples": "top, bat, ten"},
    "D": {"ipa": "/d/", "examples": "dog, bed, day"},
    "P": {"ipa": "/p/", "examples": "pat, cup, pen"},
    "B": {"ipa": "/b/", "examples": "bat, cab, big"},
    "M": {"ipa": "/m/", "examples": "man, ham, mom"},
    "N": {"ipa": "/n/", "examples": "no, sun, new"},
    "NG": {"ipa": "/ŋ/", "examples": "sing, ring, long"},
    "W": {"ipa": "/w/", "examples": "we, swim, water"},
    "Y": {"ipa": "/j/", "examples": "yes, you, yellow"},
    "HH": {"ipa": "/h/", "examples": "hat, hello, house"},
}


@dataclass
class PhonemeMatchResultEn:
    """영어 음소 매칭 결과.

    Attributes:
        matched_words: 타깃 음소가 포함된 단어 목록
        count: 매칭된 단어 수
        meets_minimum: 최소 출현 횟수 충족 여부
    """
    matched_words: list[str]
    count: int
    meets_minimum: bool = True


def get_phonemes(word: str) -> list[str]:
    """단어의 ARPAbet 음소 리스트를 반환합니다.

    Args:
        word: 영어 단어

    Returns:
        ARPAbet 음소 리스트 (강세 숫자 제거됨).
        빈 문자열이면 빈 리스트 반환.

    Examples:
        >>> get_phonemes("red")
        ['R', 'EH', 'D']
        >>> get_phonemes("cat")
        ['K', 'AE', 'T']
    """
    if not word:
        return []

    clean_word = word.lower().strip()
    if not clean_word:
        return []

    # CMUdict에서 조회
    phones = pronouncing.phones_for_word(clean_word)
    if phones:
        return [re.sub(r"[012]", "", p) for p in phones[0].split()]

    # OOV: g2p로 예측
    g2p = _get_g2p()
    predicted = g2p(clean_word)
    return [re.sub(r"[012]", "", p) for p in predicted if p.isalpha() and len(p) <= 3]


def has_target_phoneme(word: str, target: str) -> bool:
    """단어에 타깃 음소가 포함되어 있는지 확인합니다.

    Args:
        word: 영어 단어
        target: ARPAbet 음소 (R, S, TH 등)

    Returns:
        포함 여부

    Examples:
        >>> has_target_phoneme("red", "R")
        True
        >>> has_target_phoneme("cat", "R")
        False
    """
    phonemes = get_phonemes(word)
    return target.upper() in phonemes


def find_phoneme_matches_en(
    sentence: str,
    target: str,
    min_occurrences: int = 1,
) -> PhonemeMatchResultEn:
    """문장에서 타깃 음소를 포함하는 단어들을 찾습니다.

    Args:
        sentence: 영어 문장
        target: ARPAbet 음소 (R, S, TH 등)
        min_occurrences: 최소 출현 횟수

    Returns:
        PhonemeMatchResultEn 객체

    Examples:
        >>> result = find_phoneme_matches_en("The red car runs", "R", min_occurrences=2)
        >>> result.matched_words
        ['red', 'car', 'runs']
        >>> result.meets_minimum
        True
    """
    words = sentence.split()
    matched_words = []

    for word in words:
        clean = "".join(c for c in word if c.isalpha())
        if clean and has_target_phoneme(clean, target):
            matched_words.append(clean.lower())

    return PhonemeMatchResultEn(
        matched_words=matched_words,
        count=len(matched_words),
        meets_minimum=len(matched_words) >= min_occurrences,
    )
