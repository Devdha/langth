"""4단계 파이프라인 오케스트레이션.

Generate -> Validate -> Score -> Diversify 파이프라인을 실행합니다.
"""

import logging
import time
import uuid
from dataclasses import dataclass

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
    diversify_results,
)
from app.agents.guardrails import filter_unsafe_sentences

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """파이프라인 결과.

    Attributes:
        success: 성공 여부
        items: 생성된 치료 아이템들
        meta: 메타 정보 (requestedCount, generatedCount, averageScore, processingTimeMs)
    """

    success: bool
    items: list[TherapyItemV2]
    meta: dict


async def run_pipeline(
    request: GenerateRequestV2,
    max_attempts: int = 3,
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
    all_validated: list[dict] = []

    logger.info(
        f"[Pipeline] 시작 - count={request.count}, phoneme={request.target.phoneme}, "
        f"position={request.target.position}, approach={request.therapyApproach}"
    )

    # 재시도 루프
    for attempt in range(max_attempts):
        # 1. Generate
        batch_size = (request.count - len(all_validated)) * 3
        if batch_size <= 0:
            logger.info(f"[Pipeline] 시도 {attempt+1}: 충분한 문장 확보, 생성 스킵")
            break

        logger.info(f"[Pipeline] 시도 {attempt+1}/{max_attempts}: batch_size={batch_size}")

        gen_start = time.time()
        try:
            candidates = await generate_candidates(request, batch_size)
            gen_time = int((time.time() - gen_start) * 1000)
            logger.info(f"[Generate] 완료 - {len(candidates)}개 생성, {gen_time}ms")
        except Exception as e:
            gen_time = int((time.time() - gen_start) * 1000)
            logger.error(f"[Generate] 실패 - {gen_time}ms, error: {e}")
            continue

        # 가드레일: 안전하지 않은 문장 필터링
        guard_start = time.time()
        safe_candidates = filter_unsafe_sentences(candidates)
        guard_time = int((time.time() - guard_start) * 1000)
        filtered_count = len(candidates) - len(safe_candidates)
        if filtered_count > 0:
            logger.warning(f"[Guardrail] {filtered_count}개 필터링됨, {guard_time}ms")
        else:
            logger.debug(f"[Guardrail] 완료 - {guard_time}ms")

        # 2. Validate
        val_start = time.time()
        results = validate_sentences(safe_candidates, request)
        passed = get_passed_sentences(results)
        val_time = int((time.time() - val_start) * 1000)

        failed_count = len(safe_candidates) - len(passed)
        if failed_count > 0:
            # 실패 이유 로깅
            fail_reasons = {}
            for r in results:
                if not r["passed"] and r.get("fail_reason"):
                    reason = r["fail_reason"]
                    fail_reasons[reason] = fail_reasons.get(reason, 0) + 1
            logger.warning(
                f"[Validate] {len(passed)}/{len(safe_candidates)} 통과, "
                f"실패 사유: {fail_reasons}, {val_time}ms"
            )
        else:
            logger.info(f"[Validate] {len(passed)}/{len(safe_candidates)} 통과, {val_time}ms")

        all_validated.extend(passed)
        logger.info(f"[Pipeline] 시도 {attempt+1} 완료: 누적 {len(all_validated)}개")

        # 충분하면 종료
        if len(all_validated) >= request.count:
            break

    # 3. Score
    score_start = time.time()
    scored = score_sentences(all_validated, request)
    score_time = int((time.time() - score_start) * 1000)
    logger.info(f"[Score] {len(scored)}개 점수 계산, {score_time}ms")

    # 4. Diversify
    div_start = time.time()
    final = diversify_results(scored, request.count)
    div_time = int((time.time() - div_start) * 1000)
    logger.info(f"[Diversify] {len(scored)} -> {len(final)}개, {div_time}ms")

    # TherapyItemV2로 변환
    items = [_to_therapy_item(s, request) for s in final]

    processing_time = int((time.time() - start_time) * 1000)

    logger.info(
        f"[Pipeline] 완료 - {len(items)}/{request.count}개 생성, "
        f"총 {processing_time}ms"
    )

    return PipelineResult(
        success=True,
        items=items,
        meta={
            "requestedCount": request.count,
            "generatedCount": len(items),
            "averageScore": round(sum(s.score for s in final) / len(final), 2)
            if final
            else 0,
            "processingTimeMs": processing_time,
        },
    )


def _to_therapy_item(scored, request: GenerateRequestV2) -> TherapyItemV2:
    """ScoredSentence를 TherapyItemV2로 변환.

    Args:
        scored: 점수가 부여된 문장
        request: 생성 요청

    Returns:
        TherapyItemV2
    """
    # 매칭 단어 위치 계산
    matched_words = []
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
        diagnosis=request.diagnosis,
        approach=request.therapyApproach,
        theme=request.theme,
        function=request.communicativeFunction,
    )
