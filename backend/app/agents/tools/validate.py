"""문장 검증 도구.

생성된 문장들의 하드 제약(길이, 음소)을 검사합니다.
"""

from dataclasses import dataclass
import re
import string

from app.api.v2.schemas import (
    GenerateRequestV2,
    Language,
    PhonemePosition,
    TherapyApproach,
    DifficultyLevel,
)
from app.services.phoneme.korean import find_phoneme_matches
from app.services.phoneme.english import find_phoneme_matches_en
from app.services.lexical.core_vocabulary import resolve_core_words


# 한국어 형용사/동사 어간 추출을 위한 어미 패턴
_KO_VERB_ENDINGS = [
    "습니다", "ㅂ니다", "어요", "아요", "여요", "에요", "예요",
    "었어", "았어", "였어", "겠어", "을래", "ㄹ래",
    "하게", "하고", "해서", "하면", "해요", "했어",
    "어서", "아서", "으면", "면", "고", "게", "지",
    "는", "은", "ㄴ", "을", "ㄹ",
]

# 어간 그룹: 같은 의미의 활용형들을 그룹으로 묶음
# key: 대표 어간, value: 해당 어간의 모든 활용형
_KO_STEM_GROUPS: dict[str, list[str]] = {
    "맛있": ["맛있"],
    "맛없": ["맛없"],
    "예쁘": ["예쁘", "예쁜", "예뻐"],
    "이쁘": ["이쁘", "이쁜", "이뻐"],
    "좋": ["좋"],
    "싫": ["싫"],
    "크": ["크", "큰", "커"],
    "작": ["작"],
    "많": ["많"],
    "적": ["적"],
    "높": ["높"],
    "낮": ["낮"],
    "길": ["길"],
    "짧": ["짧"],
    "넓": ["넓"],
    "좁": ["좁"],
    "빠르": ["빠르", "빠른", "빨라"],
    "느리": ["느리", "느린", "느려"],
    "무겁": ["무겁", "무거운", "무거워"],
    "가볍": ["가볍", "가벼운", "가벼워"],
    "뜨겁": ["뜨겁", "뜨거운", "뜨거워"],
    "차갑": ["차갑", "차가운", "차가워"],
    "재미있": ["재미있"],
    "재미없": ["재미없"],
    "귀엽": ["귀엽", "귀여운", "귀여워"],
    "무섭": ["무섭", "무서운", "무서워"],
    "슬프": ["슬프", "슬픈", "슬퍼"],
    "기쁘": ["기쁘", "기쁜", "기뻐"],
}


def _extract_korean_stems(text: str) -> list[str]:
    """한국어 문장에서 형용사/동사 어간을 추출합니다.

    간단한 규칙 기반 추출로, 정확한 형태소 분석은 아닙니다.
    의미 반복 검출 목적으로만 사용됩니다.
    같은 어간의 활용형들은 대표 어간으로 정규화됩니다.

    Args:
        text: 분석할 문장

    Returns:
        추출된 대표 어간 리스트
    """
    stems = []

    # 각 어간 그룹에서 활용형 검색
    for representative, variants in _KO_STEM_GROUPS.items():
        count = 0
        for variant in variants:
            count += len(re.findall(re.escape(variant), text))
        # 해당 어간 그룹이 발견된 횟수만큼 대표 어간 추가
        stems.extend([representative] * count)

    return stems


def _check_semantic_repetition(sentence: str, language: Language) -> str | None:
    """의미 반복을 검사합니다.

    동일한 어간이 2회 이상 등장하면 의미 반복으로 판단합니다.
    예: "맛있는 라면을 맛있게 먹어요" → 맛있- 2회 반복

    Args:
        sentence: 검사할 문장
        language: 언어

    Returns:
        반복된 어간 (발견 시) 또는 None
    """
    if language != Language.KO:
        return None

    stems = _extract_korean_stems(sentence)

    # 어간별 출현 횟수 계산
    stem_counts: dict[str, int] = {}
    for stem in stems:
        stem_counts[stem] = stem_counts.get(stem, 0) + 1

    # 2회 이상 등장하는 어간 찾기
    for stem, count in stem_counts.items():
        if count >= 2:
            return stem

    return None


# 한국어 서술어 어미 패턴 (동사/형용사)
_KO_PREDICATE_ENDINGS = [
    # 종결어미
    "요", "어", "아", "야", "지", "래", "자", "다", "네", "나",
    "줘", "봐", "워", "써", "해", "게", "고", "며", "면",
    # 문장부호 포함
    "어!", "아!", "야!", "다!", "지!", "래!", "요!", "네!", "자!",
    "어?", "아?", "야?", "지?", "래?", "요?", "나?", "니?",
    "어~", "아~", "야~", "다~", "요~",
    # 존댓말
    "습니다", "ㅂ니다", "세요", "셔요",
    # 의문형
    "니", "냐", "까",
]


def _check_has_predicate(sentence: str, language: Language) -> bool:
    """문장에 서술어가 있는지 검사합니다.

    한국어 문장은 서술어(동사/형용사)로 끝나야 완전한 문장입니다.
    명사구만 있는 경우 불완전한 문장으로 판단합니다.

    Args:
        sentence: 검사할 문장
        language: 언어

    Returns:
        서술어가 있으면 True
    """
    if language != Language.KO:
        return True  # 영어는 별도 처리 필요

    text = sentence.strip()

    # 문장부호 제거 후 검사
    for ending in _KO_PREDICATE_ENDINGS:
        if text.endswith(ending):
            return True

    # 마지막 토큰 검사
    words = text.split()
    if words:
        last_word = words[-1].rstrip("!?~.")
        for ending in _KO_PREDICATE_ENDINGS:
            if last_word.endswith(ending):
                return True

    return False


@dataclass
class ValidationResult:
    """검증 결과.

    Attributes:
        sentence: 검증된 문장
        passed: 통과 여부
        matched_words: 타깃 음소를 포함한 단어들
        word_count: 문장의 단어/어절 수
        difficulty: 난이도 (옵션)
        fail_reason: 실패 이유 (통과 시 None)
    """
    sentence: str
    passed: bool
    matched_words: list[str]
    word_count: int
    difficulty: str | None = None
    fail_reason: str | None = None


def validate_sentences(
    sentences: list[str] | list[dict],
    request: GenerateRequestV2,
) -> list[ValidationResult]:
    """문장들의 하드 제약을 검사합니다.

    검사 항목:
    1. 길이 (어절/단어 수)
    2. 타깃 음소 포함 여부 및 위치
    3. 최소 출현 횟수

    Args:
        sentences: 검사할 문장 리스트 (문장 문자열 또는 문장 딕셔너리)
        request: 생성 요청 (조건 포함)

    Returns:
        ValidationResult 리스트

    Examples:
        >>> from app.api.v2.schemas import *
        >>> req = GenerateRequestV2(
        ...     language=Language.KO, age=5, count=10,
        ...     target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
        ...     sentenceLength=4, diagnosis=DiagnosisType.SSD, therapyApproach=TherapyApproach.MINIMAL_PAIRS
        ... )
        >>> results = validate_sentences(["라면이 너무 맛있어요"], req)
        >>> results[0].passed
        True
    """
    results = []
    normalized = []

    allowed_difficulties = {level.value for level in DifficultyLevel}

    for item in sentences:
        if isinstance(item, str):
            normalized.append({"sentence": item, "difficulty": None})
        elif isinstance(item, dict):
            sentence = item.get("sentence")
            if not isinstance(sentence, str):
                continue
            difficulty = item.get("difficulty")
            if isinstance(difficulty, str) and difficulty not in allowed_difficulties:
                difficulty = None
            normalized.append({
                "sentence": sentence,
                "difficulty": difficulty if isinstance(difficulty, str) else None,
            })

    for item in normalized:
        result = _validate_single(item["sentence"], request, item.get("difficulty"))
        results.append(result)

    return results


def _validate_single(
    sentence: str,
    request: GenerateRequestV2,
    difficulty: str | None = None,
) -> ValidationResult:
    """단일 문장 검증.

    Args:
        sentence: 검증할 문장
        request: 생성 요청

    Returns:
        ValidationResult
    """
    # 1. 길이 검사
    words = sentence.strip().split()
    word_count = len(words)

    if word_count != request.sentenceLength:
        return ValidationResult(
            sentence=sentence,
            passed=False,
            matched_words=[],
            word_count=word_count,
            difficulty=difficulty,
            fail_reason=f"word_count: expected {request.sentenceLength}, got {word_count}",
        )

    # 2. 의미 반복 검사 (한국어만)
    repeated_stem = _check_semantic_repetition(sentence, request.language)
    if repeated_stem:
        return ValidationResult(
            sentence=sentence,
            passed=False,
            matched_words=[],
            word_count=word_count,
            difficulty=difficulty,
            fail_reason=f"semantic_repetition: '{repeated_stem}' appears multiple times",
        )

    # 2.5. 서술어 체크 (짧은 문장에서만, 명사구 필터링)
    if word_count <= 3 and not _check_has_predicate(sentence, request.language):
        return ValidationResult(
            sentence=sentence,
            passed=False,
            matched_words=[],
            word_count=word_count,
            difficulty=difficulty,
            fail_reason="no_predicate: sentence lacks a predicate (verb/adjective)",
        )

    # 3. 음소 검사
    # core_vocabulary(ASD)는 기능적 의사소통이 목표이므로 음소 검증 스킵
    if request.therapyApproach == TherapyApproach.CORE_VOCABULARY:
        if request.language == Language.KO and _has_korean_spacing_antipattern(sentence):
            return ValidationResult(
                sentence=sentence,
                passed=False,
                matched_words=[],
                word_count=word_count,
                difficulty=difficulty,
                fail_reason="core_vocabulary: spacing anti-pattern",
            )
        core_words = resolve_core_words(request.language.value, request.core_words)
        if not _contains_core_word(words, core_words, request.language):
            return ValidationResult(
                sentence=sentence,
                passed=False,
                matched_words=[],
                word_count=word_count,
                difficulty=difficulty,
                fail_reason="core_vocabulary: missing core word",
            )
        return ValidationResult(
            sentence=sentence,
            passed=True,
            matched_words=[],
            word_count=word_count,
            difficulty=difficulty,
        )

    if request.target and request.target.phoneme:
        if request.language == Language.KO:
            match_result = find_phoneme_matches(
                sentence,
                request.target.phoneme,
                request.target.position.value,
                request.target.minOccurrences,
            )
        else:
            match_result = find_phoneme_matches_en(
                sentence,
                request.target.phoneme,
                request.target.minOccurrences,
            )

        if not match_result.meets_minimum:
            return ValidationResult(
                sentence=sentence,
                passed=False,
                matched_words=match_result.matched_words,
                word_count=word_count,
                difficulty=difficulty,
                fail_reason=f"phoneme: found {match_result.count}, need {request.target.minOccurrences}",
            )

        return ValidationResult(
            sentence=sentence,
            passed=True,
            matched_words=match_result.matched_words,
            word_count=word_count,
            difficulty=difficulty,
        )

    # 음소 타깃 없으면 길이만 통과하면 OK
    return ValidationResult(
        sentence=sentence,
        passed=True,
        matched_words=[],
        word_count=word_count,
        difficulty=difficulty,
    )


def _normalize_token(token: str, language: Language) -> str:
    cleaned = token.strip(string.punctuation)
    if language == Language.EN:
        return cleaned.lower()
    return cleaned


def _contains_core_word(words: list[str], core_words: list[str], language: Language) -> bool:
    if not core_words:
        return False

    normalized_words = {_normalize_token(word, language) for word in words if word}
    normalized_core = {_normalize_token(word, language) for word in core_words if word}
    normalized_words.discard("")
    normalized_core.discard("")
    return not normalized_words.isdisjoint(normalized_core)


def _has_korean_spacing_antipattern(sentence: str) -> bool:
    # e.g. "이거 뭐 야", "저거 해 줘", "이거 해 봐"
    patterns = [
        r"(뭐|왜|어디|누구|이거|저거|그거|여기|거기)\s+(야|니|냐|지|죠)\b",
        r"([가-힣]+)\s+(줘(?:요)?|줬(?:어|어요)|줄(?:래|게|까)|주(?:라|면|고|지|세요))\b",
        r"([가-힣]+)\s+봐(?:요|줘|라|)\b",
    ]
    return any(re.search(p, sentence) for p in patterns)


def get_passed_sentences(results: list[ValidationResult]) -> list[dict]:
    """통과한 문장들만 추출합니다.

    Args:
        results: ValidationResult 리스트

    Returns:
        통과한 문장 정보 딕셔너리 리스트
    """
    return [
        {
            "sentence": r.sentence,
            "matched_words": r.matched_words,
            "word_count": r.word_count,
            "difficulty": r.difficulty,
        }
        for r in results
        if r.passed
    ]
