"""FastAPI router for the v2 API.

This module defines the API endpoints for therapy sentence generation.
"""

from fastapi import APIRouter, HTTPException

from .schemas import (
    ErrorCode,
    ErrorResponseV2,
    GenerateRequestV2,
    GenerateResponseV2,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post(
    "/generate",
    response_model=GenerateResponseV2 | ErrorResponseV2,
    responses={
        501: {"model": ErrorResponseV2},
    },
)
async def generate_sentences(request: GenerateRequestV2):
    """Generate therapy sentences based on the provided configuration.

    This endpoint generates sentences for speech therapy practice using a
    4-stage pipeline:
    1. Generate: LLM generates candidate sentences
    2. Validate: Hard constraint validation
    3. Score: Quality scoring
    4. Diversify: Ensure diversity in output

    Args:
        request: The sentence generation request configuration.

    Returns:
        GenerateResponseV2 on success with generated sentences.
        ErrorResponseV2 on failure with error details.

    Raises:
        HTTPException: 501 if pipeline is not yet implemented.
    """
    # TODO: Connect to pipeline implementation
    raise HTTPException(
        status_code=501,
        detail={
            "success": False,
            "error": {
                "code": ErrorCode.SERVICE_UNAVAILABLE.value,
                "message": "Pipeline is not yet implemented.",
            },
        },
    )
