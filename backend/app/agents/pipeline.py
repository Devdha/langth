"""4단계 파이프라인 오케스트레이션.

Generate -> Validate -> Score -> Diversify 파이프라인을 실행합니다.
"""

import logging
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field

from app.api.v2.schemas import (
    GenerateRequestV2,
    TherapyItemV2,
    MatchedWord,
)
from app.agents.tools import (
    generate_candidates,
    validate_sentences,
    get_passed_sentences,
    score_sentences,
)
# Guardrail 제거됨 - 치료사가 직접 검토
from app.api.v2.schemas import Language
from app.services.phoneme.korean import find_phoneme_matches
from app.services.phoneme.english import find_phoneme_matches_en

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """파이프라인 품질 지표.

    Attributes:
        generated_count: LLM이 생성한 총 문장 수
        validation_passed: Validation 통과 문장 수
        validation_rate: Validation 통과율 (%)
        fail_reasons: 실패 이유별 카운트
        unique_structures: 고유 문장 구조 수
        vocabulary_diversity: 어휘 다양성 (고유 명사 / 총 명사)
        semantic_duplicates: 의미 반복으로 탈락한 문장 수
        final_count: 최종 후보 수
    """
    generated_count: int = 0
    validation_passed: int = 0
    validation_rate: float = 0.0
    fail_reasons: dict[str, int] = field(default_factory=dict)
    unique_structures: int = 0
    vocabulary_diversity: float = 0.0
    semantic_duplicates: int = 0
    final_count: int = 0


def _calculate_metrics(
    all_candidates: list[dict],
    validation_results: list,
    scored: list,
    language: Language,
) -> PipelineMetrics:
    """파이프라인 품질 지표를 계산합니다.

    Args:
        all_candidates: 생성된 모든 후보
        validation_results: Validation 결과
        scored: 최종 점수 매긴 문장들
        language: 언어

    Returns:
        PipelineMetrics
    """
    from app.agents.tools.score import _extract_sentence_structure, _extract_nouns

    metrics = PipelineMetrics()
    metrics.generated_count = len(all_candidates)
    metrics.validation_passed = sum(1 for r in validation_results if r.passed)
    metrics.validation_rate = (
        (metrics.validation_passed / metrics.generated_count * 100)
        if metrics.generated_count > 0 else 0.0
    )

    # 실패 이유 집계
    for r in validation_results:
        if not r.passed and r.fail_reason:
            # 실패 이유에서 카테고리 추출
            if "word_count" in r.fail_reason:
                key = "word_count"
            elif "phoneme" in r.fail_reason:
                key = "phoneme"
            elif "semantic_repetition" in r.fail_reason:
                key = "semantic_repetition"
                metrics.semantic_duplicates += 1
            elif "no_predicate" in r.fail_reason:
                key = "no_predicate"
            elif "core_vocabulary" in r.fail_reason:
                key = "core_vocabulary"
            else:
                key = "other"
            metrics.fail_reasons[key] = metrics.fail_reasons.get(key, 0) + 1

    # 구조 다양성 계산
    structures = set()
    all_nouns: list[str] = []

    for item in scored:
        structure = _extract_sentence_structure(item.sentence, language)
        structures.add(structure)

        nouns = _extract_nouns(item.sentence, language)
        all_nouns.extend(nouns)

    metrics.unique_structures = len(structures)

    # 어휘 다양성 계산
    if all_nouns:
        unique_nouns = len(set(all_nouns))
        metrics.vocabulary_diversity = unique_nouns / len(all_nouns) * 100

    metrics.final_count = len(scored)

    return metrics


def _log_metrics(metrics: PipelineMetrics) -> None:
    """파이프라인 지표를 로깅합니다."""
    fail_str = ", ".join(f"{k}={v}" for k, v in metrics.fail_reasons.items())

    logger.info(
        f"\n[Pipeline 리포트]\n"
        f"  - 생성: {metrics.generated_count}개\n"
        f"  - Validation 통과: {metrics.validation_passed}개 ({metrics.validation_rate:.0f}%)\n"
        f"  - 실패 이유: {fail_str or '없음'}\n"
        f"  - 구조 다양성: {metrics.unique_structures}종류\n"
        f"  - 어휘 다양성: {metrics.vocabulary_diversity:.0f}%\n"
        f"  - 의미 반복 탈락: {metrics.semantic_duplicates}개\n"
        f"  - 최종 후보: {metrics.final_count}개"
    )


@dataclass
class PipelineResult:
    """파이프라인 결과.

    Attributes:
        success: 성공 여부
        items: 생성된 치료 아이템들
        contrast_sets: 생성된 대조 세트들 (선택)
        meta: 메타 정보 (requestedCount, generatedCount, averageScore, processingTimeMs)
        metrics: 파이프라인 품질 지표 (선택)
    """

    success: bool
    items: list[TherapyItemV2]
    contrast_sets: list[dict] | None
    meta: dict
    metrics: PipelineMetrics | None = None


async def run_pipeline(
    request: GenerateRequestV2,
    max_attempts: int = 1,
) -> PipelineResult:
    """4단계 파이프라인을 실행합니다.

    1. Generate: LLM으로 후보 생성
    2. Validate: 하드 제약 검사
    3. Score: 점수 계산
    4. Diversify: 다양성 보장

    Args:
        request: 생성 요청
        max_attempts: 최대 재시도 횟수

    Returns:
        PipelineResult

    Examples:
        >>> result = await run_pipeline(request)
        >>> result.success
        True
    """
    start_time = time.time()
    all_candidates: list[dict] = []  # 지표용: 생성된 모든 후보
    all_validation_results: list = []  # 지표용: 모든 validation 결과
    all_validated: list[dict] = []
    all_contrast_sets: list[dict] = []

    # target이 없을 수 있음 (core_vocabulary)
    target_info = f"phoneme={request.target.phoneme}, position={request.target.position}" if request.target else "no target"
    logger.info(
        f"[Pipeline] 시작 - count={request.count}, {target_info}, approach={request.therapyApproach}"
    )

    # 유저 선택용으로 더 많은 후보 생성 (요청의 3배)
    target_candidates = request.count * 3

    # 재시도 루프
    for attempt in range(max_attempts):
        # 1. Generate
        batch_size = target_candidates - len(all_validated)
        if batch_size <= 0:
            logger.info(f"[Pipeline] 시도 {attempt+1}: 충분한 후보 확보, 생성 스킵")
            break

        # LLM 통과율 고려하여 더 많이 요청
        batch_size = int(batch_size * 1.5)
        logger.info(f"[Pipeline] 시도 {attempt+1}/{max_attempts}: batch_size={batch_size}")

        gen_start = time.time()
        try:
            gen_result = await generate_candidates(request, batch_size)
            candidates, contrast_sets = _normalize_generation_result(gen_result)
            gen_time = int((time.time() - gen_start) * 1000)
            logger.info(f"[Generate] 완료 - {len(candidates)}개 생성, contrast_sets={len(contrast_sets)}개, {gen_time}ms")
        except Exception as e:
            gen_time = int((time.time() - gen_start) * 1000)
            logger.error(f"[Generate] 실패 - {gen_time}ms, error: {e}")
            continue

        # 2. Validate (Guardrail 제거 - 치료사가 직접 검토)
        val_start = time.time()
        results = validate_sentences(candidates, request)
        passed = get_passed_sentences(results)
        val_time = int((time.time() - val_start) * 1000)

        # 지표용 데이터 수집
        all_candidates.extend(candidates)
        all_validation_results.extend(results)

        failed_count = len(candidates) - len(passed)
        if failed_count > 0:
            # 실패 이유 로깅
            fail_reasons = {}
            for r in results:
                if not r.passed and r.fail_reason:
                    # 실패 이유에서 핵심 키워드 추출
                    if "word_count" in r.fail_reason:
                        key = "word_count"
                    elif "phoneme" in r.fail_reason:
                        key = "no_phoneme"
                    elif "semantic_repetition" in r.fail_reason:
                        key = "semantic_rep"
                    elif "no_predicate" in r.fail_reason:
                        key = "no_predicate"
                    else:
                        key = "other"
                    fail_reasons[key] = fail_reasons.get(key, 0) + 1
            logger.warning(
                f"[Validate] {len(passed)}/{len(candidates)} 통과, "
                f"실패: {fail_reasons}, {val_time}ms"
            )
        else:
            logger.info(f"[Validate] {len(passed)}/{len(candidates)} 통과, {val_time}ms")

        all_validated.extend(passed)
        if contrast_sets:
            logger.debug(f"[ContrastSet] contrast_sets={len(contrast_sets)}")
            validated_sets = _validate_contrast_sets(contrast_sets, request)
            logger.debug(f"[ContrastSet] validated_sets={len(validated_sets)}")
            all_contrast_sets.extend(validated_sets)
            if len(all_contrast_sets) > request.count:
                del all_contrast_sets[request.count:]
        logger.info(f"[Pipeline] 시도 {attempt+1} 완료: 누적 {len(all_validated)}개")

        # 충분한 후보 확보 시 종료
        if len(all_validated) >= target_candidates:
            break

    # 3. Score (Diversify 제거 - 유저가 직접 선택)
    score_start = time.time()
    scored = score_sentences(all_validated, request)
    score_time = int((time.time() - score_start) * 1000)
    logger.info(f"[Score] {len(scored)}개 점수 계산, {score_time}ms")

    # 4. 지표 계산 및 로깅
    metrics = _calculate_metrics(
        all_candidates,
        all_validation_results,
        scored,
        request.language,
    )
    _log_metrics(metrics)

    # TherapyItemV2로 변환 (전체 후보 반환)
    items = [_to_therapy_item(s, request) for s in scored]

    processing_time = int((time.time() - start_time) * 1000)

    logger.info(
        f"[Pipeline] 완료 - {len(items)}개 후보 생성 (요청: {request.count}개), "
        f"총 {processing_time}ms"
    )

    return PipelineResult(
        success=True,
        items=items,
        contrast_sets=all_contrast_sets or None,
        meta={
            "requestedCount": request.count,
            "generatedCount": len(items),
            "averageScore": round(sum(s.score for s in scored) / len(scored), 2)
            if scored
            else 0,
            "processingTimeMs": processing_time,
            "validationRate": round(metrics.validation_rate, 1),
            "uniqueStructures": metrics.unique_structures,
            "vocabularyDiversity": round(metrics.vocabulary_diversity, 1),
        },
        metrics=metrics,
    )


def _to_therapy_item(scored, request: GenerateRequestV2) -> TherapyItemV2:
    """ScoredSentence를 TherapyItemV2로 변환.

    Args:
        scored: 점수가 부여된 문장
        request: 생성 요청

    Returns:
        TherapyItemV2
    """
    # 매칭 단어 위치 계산 (target이 있을 때만)
    matched_words = []
    if request.target:
        text = scored.sentence
        for word in scored.matched_words:
            start = text.find(word)
            if start >= 0:
                matched_words.append(
                    MatchedWord(
                        word=word,
                        startIndex=start,
                        endIndex=start + len(word),
                        positions=[request.target.position],
                    )
                )

    return TherapyItemV2(
        id=str(uuid.uuid4()),
        text=scored.sentence,
        target=request.target,
        matchedWords=matched_words,
        wordCount=scored.word_count,
        score=scored.score,
        difficulty=scored.difficulty,
        diagnosis=request.diagnosis,
        approach=request.therapyApproach,
        theme=request.theme,
        function=request.communicativeFunction,
    )


def _normalize_generation_result(result) -> tuple[list[dict] | list[str], list[dict]]:
    if isinstance(result, list):
        return result, []

    candidates = result.candidates if hasattr(result, "candidates") else []
    contrast_sets = result.contrast_sets if hasattr(result, "contrast_sets") else None
    return candidates, contrast_sets or []


def _validate_contrast_sets(
    contrast_sets: list[dict],
    request: GenerateRequestV2,
) -> list[dict]:
    """Validate contrast sets for minimal/maximal oppositions.

    - Target sentence must pass phoneme validation directly.
    - Both sentences must respect token length.
    - Target/contrast words must appear in their respective token lists.
    """
    validated: list[dict] = []
    for i, contrast_set in enumerate(contrast_sets):
        target_sentence = contrast_set.get("targetSentence", {})
        contrast_sentence = contrast_set.get("contrastSentence", {})
        target_text = target_sentence.get("text")
        contrast_text = contrast_sentence.get("text")
        if not isinstance(target_text, str) or not isinstance(contrast_text, str):
            logger.debug(f"[ContrastSet #{i}] 실패: text 타입 오류")
            continue

        target_tokens = target_sentence.get("tokens", [])
        contrast_tokens = contrast_sentence.get("tokens", [])
        if (
            not isinstance(target_tokens, list)
            or not isinstance(contrast_tokens, list)
            or len(target_tokens) != request.sentenceLength
            or len(contrast_tokens) != request.sentenceLength
        ):
            logger.debug(
                f"[ContrastSet #{i}] 실패: 토큰 수 불일치 - "
                f"target={len(target_tokens)}, contrast={len(contrast_tokens)}, expected={request.sentenceLength}"
            )
            continue

        # Validate target sentence has required phoneme
        if request.target and request.target.phoneme:
            if request.language == Language.KO:
                match_result = find_phoneme_matches(
                    target_text,
                    request.target.phoneme,
                    request.target.position.value,
                    request.target.minOccurrences,
                )
            else:
                match_result = find_phoneme_matches_en(
                    target_text,
                    request.target.phoneme,
                    request.target.minOccurrences,
                )
            if not match_result.meets_minimum:
                logger.debug(
                    f"[ContrastSet #{i}] 실패: 음소 불충분 - "
                    f"text='{target_text}', found={match_result.count}, need={request.target.minOccurrences}"
                )
                continue

        target_word = contrast_set.get("targetWord", "")
        contrast_word = contrast_set.get("contrastWord", "")
        # 한국어 조사가 붙을 수 있으므로 부분 매칭 허용
        if target_word and not any(target_word in token for token in target_tokens):
            logger.debug(f"[ContrastSet #{i}] 실패: targetWord '{target_word}' not found in tokens {target_tokens}")
            continue
        if contrast_word and not any(contrast_word in token for token in contrast_tokens):
            logger.debug(f"[ContrastSet #{i}] 실패: contrastWord '{contrast_word}' not found in tokens {contrast_tokens}")
            continue

        validated.append(contrast_set)

    return validated
