"""문장 점수 계산 도구.

검증된 문장들에 점수를 부여합니다.
점수 구성: 기본 비중은 빈도(40%) + 기능(30%) + 매칭보너스(20%) + 길이적합성(10%)
단, 언어/치료 접근에 따라 사용 가능한 항목만 남기고 비중을 재정규화합니다.

다양성 페널티: 이미 선택된 문장과 구조/어휘가 유사하면 점수 차감
"""

from dataclasses import dataclass
import re

from app.api.v2.schemas import (
    GenerateRequestV2,
    Language,
    CommunicativeFunction,
    TherapyApproach,
)
from app.services.corpus.korean_freq import get_sentence_frequency_score


# 한국어 조사 패턴 (구조 추출용)
_KO_PARTICLES = [
    "은", "는", "이", "가", "을", "를", "에", "에서", "으로", "로",
    "와", "과", "하고", "이랑", "랑", "도", "만", "까지", "부터",
    "의", "에게", "한테", "께", "보다",
]

# 한국어 명사 추출용 패턴 (간단한 규칙 기반)
_KO_NOUN_ENDINGS = [
    "이", "가", "은", "는", "을", "를", "에", "에서", "으로", "로",
    "와", "과", "도", "만", "의", "에게", "한테",
]


def _extract_sentence_structure(sentence: str, language: Language) -> str:
    """문장의 구조 패턴을 추출합니다.

    예: "강아지가 밥을 먹어요" → "N가 N을 V요"

    Args:
        sentence: 분석할 문장
        language: 언어

    Returns:
        구조 패턴 문자열
    """
    if language != Language.KO:
        # 영어는 단순히 품사 패턴으로 (미구현)
        return sentence.lower()

    words = sentence.strip().split()
    structure_parts = []

    for word in words:
        # 조사로 끝나는지 확인
        found_particle = None
        for particle in sorted(_KO_PARTICLES, key=len, reverse=True):
            if word.endswith(particle) and len(word) > len(particle):
                found_particle = particle
                break

        if found_particle:
            structure_parts.append(f"N{found_particle}")
        elif word.endswith(("요", "어", "아", "야", "다", "지", "네", "래")):
            structure_parts.append("V")
        elif word.endswith(("!", "?", "~")):
            # 문장 부호 포함 어미
            structure_parts.append("V" + word[-1])
        else:
            structure_parts.append("X")

    return " ".join(structure_parts)


def _extract_nouns(sentence: str, language: Language) -> set[str]:
    """문장에서 명사를 추출합니다.

    간단한 규칙 기반으로, 조사를 제거하여 명사를 추출합니다.

    Args:
        sentence: 분석할 문장
        language: 언어

    Returns:
        추출된 명사 집합
    """
    if language != Language.KO:
        # 영어는 단순히 단어 집합 반환
        return set(sentence.lower().split())

    words = sentence.strip().split()
    nouns = set()

    for word in words:
        # 조사 제거
        noun = word
        for ending in sorted(_KO_NOUN_ENDINGS, key=len, reverse=True):
            if word.endswith(ending) and len(word) > len(ending):
                noun = word[:-len(ending)]
                break

        # 너무 짧은 건 제외 (조사만 남은 경우)
        if len(noun) >= 2:
            nouns.add(noun)

    return nouns


def _calculate_diversity_penalty(
    sentence: str,
    already_scored: list["ScoredSentence"],
    language: Language,
) -> float:
    """다양성 페널티를 계산합니다.

    이미 점수가 높은 문장들과 구조/어휘가 유사하면 페널티를 부여합니다.

    Args:
        sentence: 현재 문장
        already_scored: 이미 점수 매긴 문장들 (점수순)
        language: 언어

    Returns:
        페널티 점수 (0 이상, 높을수록 나쁨)
    """
    if not already_scored:
        return 0.0

    penalty = 0.0
    current_structure = _extract_sentence_structure(sentence, language)
    current_nouns = _extract_nouns(sentence, language)

    # 상위 10개 문장과만 비교 (성능 고려)
    compare_count = min(10, len(already_scored))

    for scored in already_scored[:compare_count]:
        other_structure = _extract_sentence_structure(scored.sentence, language)
        other_nouns = _extract_nouns(scored.sentence, language)

        # 구조 유사도 페널티
        if current_structure == other_structure:
            penalty += 10.0

        # 어휘 중복 페널티 (중복 명사 1개당 5점)
        if current_nouns and other_nouns:
            overlap = current_nouns & other_nouns
            penalty += len(overlap) * 5.0

    return penalty


@dataclass
class ScoredSentence:
    """점수가 부여된 문장.

    Attributes:
        sentence: 문장 텍스트
        matched_words: 타깃 음소 포함 단어들
        word_count: 단어/어절 수
        difficulty: 난이도 (옵션)
        score: 종합 점수 (0-100)
        breakdown: 점수 breakdown (frequency, function, match_bonus, length_fit)
    """
    sentence: str
    matched_words: list[str]
    word_count: int
    difficulty: str | None
    score: float
    breakdown: dict[str, float]


# 의사소통 기능 패턴 (한국어)
FUNCTION_PATTERNS_KO = {
    CommunicativeFunction.REQUEST: [
        r"줘|주세요|줄래|싶어|싶어요|하고\s*싶|먹고\s*싶|갖고\s*싶",
    ],
    CommunicativeFunction.REJECT: [
        r"싫어|싫어요|안\s*해|안\s*할래|하기\s*싫|안\s*먹|안\s*갈",
    ],
    CommunicativeFunction.HELP: [
        r"도와|도와줘|도와주세요|어떻게|어떡해|모르겠|못\s*하겠",
    ],
    CommunicativeFunction.CHOICE: [
        r"할래\?|먹을래\?|갈래\?|이거\s*저거|뭐\s*할|어떤\s*거",
    ],
    CommunicativeFunction.ATTENTION: [
        r"봐봐|이거\s*봐|저거\s*봐|여기\s*봐|보세요|있어요",
    ],
    CommunicativeFunction.QUESTION: [
        r"뭐야|뭐예요|어디|언제|누가|왜|어떻게|\?$",
    ],
}


BASE_SCORE_WEIGHTS = {
    "frequency": 0.4,
    "function": 0.3,
    "match_bonus": 0.2,
    "length_fit": 0.1,
}


def score_sentences(
    validated: list[dict],
    request: GenerateRequestV2,
) -> list[ScoredSentence]:
    """검증된 문장들에 점수를 부여합니다.

    점수 구성:
    - frequency: 단어 빈도 점수 (기본 40%, KO 전용)
    - function: 의사소통 기능 매칭 점수 (기본 30%, KO + 기능 지정 시)
    - match_bonus: 타깃 음소 다중 매칭 보너스 (기본 20%, core_vocabulary 제외)
    - length_fit: 길이 적합성 (기본 10%, 항상 사용)
    - diversity_penalty: 구조/어휘 중복 페널티 (음수로 차감)

    사용 불가능한 항목은 비중을 0으로 두고, 남은 비중을 합이 1이 되도록 재정규화합니다.
    다양성 페널티는 가중치 적용 후 최종 점수에서 차감됩니다.

    Args:
        validated: 검증 통과한 문장들 (dict with sentence, matched_words, word_count, difficulty)
        request: 생성 요청

    Returns:
        점수순 정렬된 ScoredSentence 리스트 (다양성 고려)

    Examples:
        >>> validated = [{"sentence": "라면이 너무 맛있어요", "matched_words": ["라면이"], "word_count": 4}]
        >>> results = score_sentences(validated, request)
        >>> results[0].score > 0
        True
    """
    # 1차: 기본 점수 계산
    preliminary_results = []

    for item in validated:
        sentence = item["sentence"]
        matched_words = item["matched_words"]
        word_count = item["word_count"]
        difficulty = item.get("difficulty")

        breakdown = _calculate_breakdown(sentence, matched_words, request)
        weights = _get_score_weights(request)
        base_score = (
            breakdown["frequency"] * weights["frequency"]
            + breakdown["function"] * weights["function"]
            + breakdown["match_bonus"] * weights["match_bonus"]
            + breakdown["length_fit"] * weights["length_fit"]
        )

        preliminary_results.append({
            "sentence": sentence,
            "matched_words": matched_words,
            "word_count": word_count,
            "difficulty": difficulty,
            "base_score": base_score,
            "breakdown": breakdown,
        })

    # 기본 점수순 정렬
    preliminary_results.sort(key=lambda x: x["base_score"], reverse=True)

    # 2차: 다양성 페널티 적용하면서 최종 결과 생성
    final_results: list[ScoredSentence] = []

    for item in preliminary_results:
        # 이미 선택된 문장들과 비교하여 다양성 페널티 계산
        diversity_penalty = _calculate_diversity_penalty(
            item["sentence"],
            final_results,
            request.language,
        )

        # 페널티 적용 (최대 50점까지만 차감)
        final_score = max(0, item["base_score"] - min(diversity_penalty, 50))

        # breakdown에 다양성 페널티 추가
        breakdown = item["breakdown"].copy()
        breakdown["diversity_penalty"] = -round(diversity_penalty, 2)

        final_results.append(ScoredSentence(
            sentence=item["sentence"],
            matched_words=item["matched_words"],
            word_count=item["word_count"],
            difficulty=item["difficulty"],
            score=round(final_score, 2),
            breakdown=breakdown,
        ))

    # 최종 점수순 재정렬
    final_results.sort(key=lambda x: x.score, reverse=True)
    return final_results


def _get_score_weights(request: GenerateRequestV2) -> dict[str, float]:
    """요청 조건에 맞는 점수 가중치 반환.

    EN은 빈도/기능 점수 미구현이므로 해당 비중을 제외하고 재정규화합니다.
    core_vocabulary는 음소 매칭 보너스가 없으므로 match_bonus 비중을 제외합니다.
    """
    weights = BASE_SCORE_WEIGHTS.copy()

    if request.language != Language.KO:
        weights["frequency"] = 0.0
        weights["function"] = 0.0
    elif not request.communicativeFunction:
        weights["function"] = 0.0

    if request.therapyApproach == TherapyApproach.CORE_VOCABULARY:
        weights["match_bonus"] = 0.0

    total = sum(weights.values())
    if total <= 0:
        return {
            "frequency": 0.0,
            "function": 0.0,
            "match_bonus": 0.0,
            "length_fit": 1.0,
        }

    return {key: value / total for key, value in weights.items()}


def _calculate_breakdown(
    sentence: str,
    matched_words: list[str],
    request: GenerateRequestV2,
) -> dict[str, float]:
    """점수 breakdown 계산.

    Args:
        sentence: 문장
        matched_words: 매칭된 단어들
        request: 요청 정보

    Returns:
        각 항목별 점수 딕셔너리
    """
    # 1. 빈도 점수
    if request.language == Language.KO:
        frequency = get_sentence_frequency_score(sentence)
    else:
        frequency = 50.0  # 영어는 추후 구현

    # 2. 기능 점수
    function = 0.0
    if request.communicativeFunction and request.language == Language.KO:
        patterns = FUNCTION_PATTERNS_KO.get(request.communicativeFunction, [])
        for pattern in patterns:
            if re.search(pattern, sentence):
                function = 100.0
                break

    # 3. 매칭 보너스 (다중 매칭 시 가산)
    match_bonus = min(len(matched_words) * 30, 100)

    # 4. 길이 적합성 (항상 100, 이미 검증됨)
    length_fit = 100.0

    return {
        "frequency": round(frequency, 2),
        "function": function,
        "match_bonus": float(match_bonus),
        "length_fit": length_fit,
    }
