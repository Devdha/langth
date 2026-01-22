"""Lexical scoring service for Korean child vocabulary.

한국어 아동 어휘의 빈도 및 연령 적절성을 평가합니다.
"""

from dataclasses import dataclass

from .vocabulary import (
    WORD_FREQUENCY,
    get_word_age_level,
    get_all_vocabulary_up_to_age,
)


@dataclass
class LexicalScore:
    """문장의 어휘 점수 결과.

    Attributes:
        frequency_score: 평균 어휘 빈도 점수 (0~1)
        age_score: 평균 연령 적절성 점수 (0~1)
        overall: 종합 점수 (0~1)
        difficult_words: 연령에 어려운 단어 목록
    """
    frequency_score: float
    age_score: float
    overall: float
    difficult_words: list[str]


# 기본 빈도 점수 (데이터에 없는 단어)
DEFAULT_FREQUENCY = 0.5

# 연령별 점수 감소 계수 (연령 차이당)
AGE_PENALTY_PER_YEAR = 0.15


def _normalize_word(word: str) -> str:
    """단어를 기본형으로 정규화합니다.

    동사/형용사의 활용형을 어간으로 변환 시도합니다.

    Args:
        word: 정규화할 단어

    Returns:
        정규화된 단어 (어간 또는 원본)
    """
    # 불규칙 활용 처리 (하다 -> 해요, 했어요 등)
    irregular_mappings = {
        "해요": "하다",
        "해": "하다",
        "했어요": "하다",
        "했어": "하다",
        "하세요": "하다",
        "합니다": "하다",
    }

    if word in irregular_mappings:
        return irregular_mappings[word]

    # 일반적인 용언 어미 패턴 (길이 순 정렬 - 긴 것부터)
    verb_endings = [
        # 4글자 이상 어미
        "었어요", "았어요", "겠어요", "을게요",
        # 3글자 어미
        "습니다", "세요", "어요", "아요", "예요", "이에요",
        # 2글자 어미
        "어", "아", "니", "지", "고", "면", "서", "다",
        "요", "네", "래", "자", "까",
    ]

    for ending in verb_endings:
        if word.endswith(ending) and len(word) > len(ending):
            stem = word[:-len(ending)]
            # 최소 1글자 이상 어간 필요
            if len(stem) >= 1:
                # "다"를 붙여서 기본형 반환
                return stem + "다"

    return word


def get_word_frequency(word: str) -> float:
    """단어의 빈도 점수를 반환합니다.

    Args:
        word: 한국어 단어

    Returns:
        0~1 사이 빈도 점수. 높을수록 자주 사용되는 단어.
        데이터에 없는 단어는 0.5 (중간값) 반환.

    Examples:
        >>> get_word_frequency("엄마")
        0.98
        >>> get_word_frequency("과학자")
        0.35
        >>> get_word_frequency("알수없는단어")
        0.5
    """
    # 정확히 일치하는 경우
    if word in WORD_FREQUENCY:
        return WORD_FREQUENCY[word]

    # 동사/형용사 활용형 -> 기본형 변환 시도
    normalized = _normalize_word(word)
    if normalized in WORD_FREQUENCY:
        return WORD_FREQUENCY[normalized]

    # 조사/어미 제거 시도 (간단 버전)
    # 긴 접두어부터 검색하여 어근 찾기
    for length in range(len(word) - 1, 0, -1):
        prefix = word[:length]
        if prefix in WORD_FREQUENCY:
            return WORD_FREQUENCY[prefix]

    return DEFAULT_FREQUENCY


def get_age_appropriateness(word: str, age: int) -> float:
    """단어의 연령 적절성 점수를 반환합니다.

    Args:
        word: 한국어 단어
        age: 아동 연령 (3-7)

    Returns:
        0~1 사이 연령 적절성 점수.
        - 1.0: 완벽히 적합 (해당 연령 이하 어휘)
        - 0.7-0.9: 약간 어려움 (1-2세 높은 어휘)
        - 0.4-0.6: 어려움 (3-4세 높은 어휘)
        - 0.2 이하: 매우 어려움

    Examples:
        >>> get_age_appropriateness("엄마", 3)  # 3세 어휘, 3세 아동
        1.0
        >>> get_age_appropriateness("학교", 5)  # 7세 어휘, 5세 아동
        0.7
        >>> get_age_appropriateness("알수없는단어", 5)
        0.5
    """
    # 연령 범위 검증
    age = max(3, min(7, age))

    # 먼저 원본 단어로 검색
    word_age = get_word_age_level(word)

    # 없으면 정규화된 형태로 재시도
    if word_age is None:
        normalized = _normalize_word(word)
        if normalized != word:
            word_age = get_word_age_level(normalized)

    # 데이터에 없는 단어
    if word_age is None:
        # 빈도 기반 추정: 고빈도면 쉬운 단어로 추정
        freq = get_word_frequency(word)
        if freq >= 0.8:
            return 0.9  # 고빈도 -> 아마 쉬운 단어
        elif freq >= 0.6:
            return 0.7
        elif freq >= 0.4:
            return 0.5
        else:
            return 0.4  # 저빈도 -> 아마 어려운 단어

    # 연령 차이 계산
    age_diff = word_age - age

    if age_diff <= 0:
        # 해당 연령 이하 어휘 -> 완벽히 적합
        return 1.0
    else:
        # 연령보다 높은 어휘 -> 점수 감소
        score = 1.0 - (age_diff * AGE_PENALTY_PER_YEAR)
        return max(0.1, score)  # 최소 0.1


def _extract_tokens(tokens: list[str]) -> list[str]:
    """토큰 리스트를 정리합니다.

    조사, 어미, 구두점 등을 필터링합니다.

    Args:
        tokens: 토큰 리스트

    Returns:
        정리된 토큰 리스트
    """
    # 제외할 조사/어미 패턴
    particles = {
        "이", "가", "은", "는", "을", "를", "의", "에", "에서", "로", "으로",
        "와", "과", "하고", "랑", "이랑", "도", "만", "부터", "까지", "보다",
        "처럼", "같이", "한테", "에게", "께", "더러", "마저", "조차", "밖에",
    }

    # 구두점
    punctuation = {".", ",", "!", "?", "~", "...", "ㅋㅋ", "ㅎㅎ", "^^"}

    result = []
    for token in tokens:
        token = token.strip()
        # 빈 토큰, 구두점 제외
        if not token or token in punctuation:
            continue
        # 순수 조사 제외 (1-2글자 조사만)
        if len(token) <= 2 and token in particles:
            continue
        result.append(token)

    return result


def score_sentence_lexical(tokens: list[str], age: int) -> dict:
    """문장의 어휘(lexical) 점수를 계산합니다.

    Args:
        tokens: 단어 토큰 리스트
        age: 아동 연령 (3-7)

    Returns:
        dict with keys:
            - frequency_score: 평균 어휘 빈도 점수 (0~1)
            - age_score: 평균 연령 적절성 점수 (0~1)
            - overall: 종합 점수 (빈도 30% + 연령 70%)
            - difficult_words: 연령에 어려운 단어 목록

    Examples:
        >>> score_sentence_lexical(["엄마", "가", "밥", "을", "먹어요"], 3)
        {
            "frequency_score": 0.93,
            "age_score": 1.0,
            "overall": 0.979,
            "difficult_words": []
        }
    """
    # 토큰 정리
    clean_tokens = _extract_tokens(tokens)

    if not clean_tokens:
        return {
            "frequency_score": 0.5,
            "age_score": 0.5,
            "overall": 0.5,
            "difficult_words": [],
        }

    # 연령 범위 검증
    age = max(3, min(7, age))

    # 해당 연령까지의 적합 어휘
    appropriate_vocab = get_all_vocabulary_up_to_age(age)

    frequency_scores = []
    age_scores = []
    difficult_words = []

    for token in clean_tokens:
        # 빈도 점수
        freq_score = get_word_frequency(token)
        frequency_scores.append(freq_score)

        # 연령 적절성 점수
        age_score = get_age_appropriateness(token, age)
        age_scores.append(age_score)

        # 어려운 단어 식별 (원본과 정규화 형태 모두 확인)
        word_age = get_word_age_level(token)
        if word_age is None:
            normalized = _normalize_word(token)
            if normalized != token:
                word_age = get_word_age_level(normalized)

        if word_age is not None and word_age > age:
            difficult_words.append(token)
        elif word_age is None and age_score < 0.6:
            # 데이터에 없지만 어려워 보이는 단어
            difficult_words.append(token)

    # 평균 계산
    avg_frequency = sum(frequency_scores) / len(frequency_scores)
    avg_age = sum(age_scores) / len(age_scores)

    # 종합 점수: 연령 적절성 가중치 높게
    overall = (avg_frequency * 0.3) + (avg_age * 0.7)

    return {
        "frequency_score": round(avg_frequency, 3),
        "age_score": round(avg_age, 3),
        "overall": round(overall, 3),
        "difficult_words": difficult_words,
    }


def analyze_vocabulary_difficulty(sentence: str, age: int) -> dict:
    """문장의 어휘 난이도를 분석합니다.

    간단한 공백 기반 토큰화를 사용하는 편의 함수입니다.

    Args:
        sentence: 분석할 문장
        age: 아동 연령 (3-7)

    Returns:
        score_sentence_lexical과 동일한 형식의 결과

    Examples:
        >>> analyze_vocabulary_difficulty("엄마가 밥을 먹어요", 3)
        {"frequency_score": 0.93, "age_score": 1.0, ...}
    """
    tokens = sentence.split()
    return score_sentence_lexical(tokens, age)
