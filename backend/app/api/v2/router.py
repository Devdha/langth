"""v2 API 라우터.

치료용 문장 생성 API 엔드포인트를 제공합니다.
"""

import logging

from fastapi import APIRouter, HTTPException

from .schemas import (
    ErrorCode,
    ErrorResponseV2,
    GenerateRequestV2,
    GenerateResponseV2,
)
from app.agents.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post(
    "/generate",
    response_model=GenerateResponseV2 | ErrorResponseV2,
    responses={
        500: {"model": ErrorResponseV2},
    },
)
async def generate_sentences(request: GenerateRequestV2):
    """치료용 문장을 생성합니다.

    4단계 파이프라인:
    1. Generate: LLM으로 후보 생성
    2. Validate: 하드 제약 검사
    3. Score: 점수 계산
    4. Diversify: 다양성 보장

    Args:
        request: 생성 요청

    Returns:
        성공 시: {success: true, data: {items, meta}}
        실패 시: HTTPException with error details
    """
    try:
        result = await run_pipeline(request)

        return {
            "success": True,
            "data": {
                "items": [item.model_dump() for item in result.items],
                "contrastSets": result.contrast_sets,
                "meta": result.meta,
            },
        }
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.GENERATION_FAILED.value,
                    "message": "문장 생성에 실패했습니다.",
                    "details": str(e),
                },
            },
        )
