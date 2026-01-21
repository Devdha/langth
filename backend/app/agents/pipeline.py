"""4단계 파이프라인 오케스트레이션.

Generate -> Validate -> Score -> Diversify 파이프라인을 실행합니다.
"""

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

    # 재시도 루프
    for attempt in range(max_attempts):
        # 1. Generate
        batch_size = (request.count - len(all_validated)) * 3
        if batch_size <= 0:
            break

        candidates = await generate_candidates(request, batch_size)

        # 2. Validate
        results = validate_sentences(candidates, request)
        passed = get_passed_sentences(results)
        all_validated.extend(passed)

        # 충분하면 종료
        if len(all_validated) >= request.count:
            break

    # 3. Score
    scored = score_sentences(all_validated, request)

    # 4. Diversify
    final = diversify_results(scored, request.count)

    # TherapyItemV2로 변환
    items = [_to_therapy_item(s, request) for s in final]

    processing_time = int((time.time() - start_time) * 1000)

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
