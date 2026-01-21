"""Tests for the v2 API endpoints.

This module tests the v2 API schema validation and endpoint behavior.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Health check should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestGenerateEndpointValidation:
    """Tests for /api/v2/generate endpoint validation."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Should return 422 when required fields are missing."""
        response = await client.post("/api/v2/generate", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_language(self, client):
        """Should return 422 for invalid language code."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "invalid",
                "age": 5,
                "count": 10,
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "SSD",
                "therapyApproach": "minimal_pairs",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_request_structure(self, client):
        """Should accept valid request structure (returns 501 until pipeline is implemented)."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 5,
                "count": 5,
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "SSD",
                "therapyApproach": "minimal_pairs",
            },
        )
        # Pipeline not implemented yet, so 501 is expected
        assert response.status_code in [200, 501]

    @pytest.mark.asyncio
    async def test_invalid_age(self, client):
        """Should return 422 for invalid age value."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 10,  # Invalid: only 3-7 allowed
                "count": 5,
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "SSD",
                "therapyApproach": "minimal_pairs",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_count_too_high(self, client):
        """Should return 422 when count exceeds maximum."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 5,
                "count": 25,  # Invalid: max is 20
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "SSD",
                "therapyApproach": "minimal_pairs",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_diagnosis(self, client):
        """Should return 422 for invalid diagnosis type."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 5,
                "count": 5,
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "INVALID",
                "therapyApproach": "minimal_pairs",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_therapy_approach(self, client):
        """Should return 422 for invalid therapy approach."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 5,
                "count": 5,
                "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
                "sentenceLength": 4,
                "diagnosis": "SSD",
                "therapyApproach": "invalid_approach",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_english_request(self, client):
        """Should accept valid English request."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "en",
                "age": 4,
                "count": 3,
                "target": {"phoneme": "r", "position": "onset", "minOccurrences": 2},
                "sentenceLength": 3,
                "diagnosis": "ASD",
                "therapyApproach": "core_vocabulary",
            },
        )
        assert response.status_code in [200, 501]

    @pytest.mark.asyncio
    async def test_optional_fields(self, client):
        """Should accept request with optional fields."""
        response = await client.post(
            "/api/v2/generate",
            json={
                "language": "ko",
                "age": 6,
                "count": 10,
                "target": {"phoneme": "ㅅ", "position": "coda", "minOccurrences": 1},
                "sentenceLength": 5,
                "diagnosis": "LD",
                "therapyApproach": "complexity",
                "theme": "animals",
                "communicativeFunction": "request",
            },
        )
        assert response.status_code in [200, 501]
