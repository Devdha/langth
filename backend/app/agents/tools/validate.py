"""문장 검증 도구.

생성된 문장들의 하드 제약(길이, 음소)을 검사합니다.
"""

from dataclasses import dataclass

from app.api.v2.schemas import GenerateRequestV2, Language, PhonemePosition, TherapyApproach
from app.services.phoneme.korean import find_phoneme_matches
from app.services.phoneme.english import find_phoneme_matches_en


@dataclass
class ValidationResult:
    """검증 결과.

    Attributes:
        sentence: 검증된 문장
        passed: 통과 여부
        matched_words: 타깃 음소를 포함한 단어들
        word_count: 문장의 단어/어절 수
        fail_reason: 실패 이유 (통과 시 None)
    """
    sentence: str
    passed: bool
    matched_words: list[str]
    word_count: int
    fail_reason: str | None = None


def validate_sentences(
    sentences: list[str],
    request: GenerateRequestV2,
) -> list[ValidationResult]:
    """문장들의 하드 제약을 검사합니다.

    검사 항목:
    1. 길이 (어절/단어 수)
    2. 타깃 음소 포함 여부 및 위치
    3. 최소 출현 횟수

    Args:
        sentences: 검사할 문장 리스트
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

    for sentence in sentences:
        result = _validate_single(sentence, request)
        results.append(result)

    return results


def _validate_single(sentence: str, request: GenerateRequestV2) -> ValidationResult:
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
            fail_reason=f"word_count: expected {request.sentenceLength}, got {word_count}",
        )

    # 2. 음소 검사
    # core_vocabulary(ASD)는 기능적 의사소통이 목표이므로 음소 검증 스킵
    if request.therapyApproach == TherapyApproach.CORE_VOCABULARY:
        return ValidationResult(
            sentence=sentence,
            passed=True,
            matched_words=[],
            word_count=word_count,
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
                fail_reason=f"phoneme: found {match_result.count}, need {request.target.minOccurrences}",
            )

        return ValidationResult(
            sentence=sentence,
            passed=True,
            matched_words=match_result.matched_words,
            word_count=word_count,
        )

    # 음소 타깃 없으면 길이만 통과하면 OK
    return ValidationResult(
        sentence=sentence,
        passed=True,
        matched_words=[],
        word_count=word_count,
    )


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
        }
        for r in results
        if r.passed
    ]
