"""파이프라인 오케스트레이션 테스트.

4단계 파이프라인 테스트:
1. Generate: LLM으로 후보 생성
2. Validate: 하드 제약 검사
3. Score: 점수 계산
4. Diversify: 다양성 보장
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.pipeline import run_pipeline
from app.agents.tools.generate import GenerateCandidatesResult
from app.api.v2.schemas import (
    GenerateRequestV2,
    TargetConfig,
    PhonemePosition,
    Language,
    DiagnosisType,
    TherapyApproach,
)


@pytest.fixture
def gen_request():
    """테스트용 생성 요청."""
    return GenerateRequestV2(
        language=Language.KO,
        age=5,
        count=5,
        target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
        sentenceLength=4,
        diagnosis=DiagnosisType.SSD,
        therapyApproach=TherapyApproach.MINIMAL_PAIRS,
    )


class TestRunPipeline:
    """run_pipeline 테스트."""

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_returns_items(self, mock_generate, gen_request):
        """파이프라인이 아이템 반환."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[
                {"sentence": "라면이 너무 맛있어요"},
                {"sentence": "라볶이를 먹고 싶어요"},
                {"sentence": "달리기가 재미있어요"},
                {"sentence": "물을 마시고 싶어요"},
                {"sentence": "길을 걸어가고 있어요"},
                {"sentence": "라면을 끓이고 있어요"},
            ]
        )

        result = await run_pipeline(gen_request)

        assert result.success is True
        assert len(result.items) <= gen_request.count
        assert result.meta["requestedCount"] == gen_request.count

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_handles_insufficient(self, mock_generate, gen_request):
        """부족한 결과 처리."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[
                {"sentence": "사과가 맛있어요"},  # ㄹ 없음, 3어절
            ]
        )

        result = await run_pipeline(gen_request)

        # 조건에 맞는 문장이 부족해도 에러 아님
        assert result.success is True
        assert result.meta["generatedCount"] < result.meta["requestedCount"]

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_retries_on_insufficient(self, mock_generate, gen_request):
        """부족 시 재시도."""
        # 첫 호출: 부족, 두 번째 호출: 충분, 세 번째 호출: 추가 (max_attempts=3)
        mock_generate.side_effect = [
            GenerateCandidatesResult(candidates=[{"sentence": "사과가 맛있어요"}]),
            GenerateCandidatesResult(
                candidates=[
                    {"sentence": "라면이 너무 맛있어요"},
                    {"sentence": "달리기가 재미있어요"},
                ]
            ),
            GenerateCandidatesResult(
                candidates=[
                    {"sentence": "라볶이를 먹고 싶어요"},
                    {"sentence": "물을 마시고 싶어요"},
                    {"sentence": "길을 걸어가고 있어요"},
                ]
            ),
        ]

        result = await run_pipeline(gen_request)

        # 재시도가 발생해야 함
        assert mock_generate.call_count >= 2

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_returns_therapy_items(self, mock_generate, gen_request):
        """TherapyItemV2 형식으로 반환."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[
                {"sentence": "라면이 너무 맛있어요"},
            ]
        )

        result = await run_pipeline(gen_request)

        if result.items:
            item = result.items[0]
            assert item.id is not None
            assert item.text == "라면이 너무 맛있어요"
            assert item.target == gen_request.target
            assert item.diagnosis == gen_request.diagnosis
            assert item.approach == gen_request.therapyApproach

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_preserves_difficulty(self, mock_generate, gen_request):
        """난이도 메타데이터 보존."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[
                {"sentence": "라면이 너무 맛있어요", "difficulty": "easy"},
            ]
        )

        result = await run_pipeline(gen_request)

        if result.items:
            assert result.items[0].difficulty == "easy"

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_meta_includes_processing_time(self, mock_generate, gen_request):
        """메타에 처리 시간 포함."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[{"sentence": "라면이 너무 맛있어요"}]
        )

        result = await run_pipeline(gen_request)

        assert "processingTimeMs" in result.meta
        assert isinstance(result.meta["processingTimeMs"], int)
        assert result.meta["processingTimeMs"] >= 0

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_meta_includes_average_score(self, mock_generate, gen_request):
        """메타에 평균 점수 포함."""
        mock_generate.return_value = GenerateCandidatesResult(
            candidates=[
                {"sentence": "라면이 너무 맛있어요"},
                {"sentence": "달리기가 재미있어요"},
            ]
        )

        result = await run_pipeline(gen_request)

        assert "averageScore" in result.meta
        if result.items:
            assert result.meta["averageScore"] > 0

    @pytest.mark.asyncio
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_empty_result(self, mock_generate, gen_request):
        """빈 결과 처리."""
        mock_generate.return_value = GenerateCandidatesResult(candidates=[])

        result = await run_pipeline(gen_request)

        assert result.success is True
        assert result.items == []
        assert result.meta["generatedCount"] == 0
        assert result.meta["averageScore"] == 0
