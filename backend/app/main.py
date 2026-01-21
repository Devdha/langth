"""Main FastAPI application for Talk Talk Vending API v2."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v2.router import router as v2_router
from app.config import settings

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
