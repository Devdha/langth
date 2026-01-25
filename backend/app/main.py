"""Main FastAPI application for Talk Talk Vending API v2."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v2.router import router as v2_router
from app.config import settings

# 로깅 설정
log_level = logging.DEBUG if settings.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# 외부 라이브러리 로깅 레벨 조정
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info(f"로깅 초기화 완료 - level={logging.getLevelName(log_level)}")

app = FastAPI(
    title="Talk Talk Vending API v2",
    version="2.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(v2_router)


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status and version information.
    """
    return {"status": "healthy", "version": "2.0.0"}
