import pytest
from app.agents.tools.diversify import diversify_results
from app.agents.tools.score import ScoredSentence


@pytest.fixture
def scored_sentences():
    return [
        ScoredSentence("라면이 너무 맛있어요", ["라면이"], 4, 85.0, {}),
        ScoredSentence("라면을 먹고 싶어요", ["라면을"], 4, 82.0, {}),
        ScoredSentence("라면이랑 김치 먹자", ["라면이랑"], 4, 80.0, {}),
        ScoredSentence("달리기를 하고 싶어요", ["달리기를"], 4, 78.0, {}),
        ScoredSentence("달리기가 재미있어요", ["달리기가"], 4, 75.0, {}),
        ScoredSentence("물을 마시고 싶어요", ["물을"], 4, 72.0, {}),
    ]


class TestDiversifyResults:
    def test_returns_requested_count(self, scored_sentences):
        """요청한 개수만큼 반환"""
        results = diversify_results(scored_sentences, count=3)
        assert len(results) == 3

    def test_respects_max_similar(self, scored_sentences):
        """유사 문장 제한"""
        results = diversify_results(scored_sentences, count=5, max_similar=2)

        # "라면" 포함 문장이 2개 이하여야 함
        ramen_count = sum(1 for r in results if "라면" in r.sentence)
        assert ramen_count <= 2

    def test_maintains_score_priority(self, scored_sentences):
        """점수 우선순위 유지 (다양성 내에서)"""
        results = diversify_results(scored_sentences, count=3)

        # 최고 점수 문장이 포함되어야 함
        assert any(r.score == 85.0 for r in results)

    def test_handles_fewer_than_requested(self):
        """요청보다 적은 문장"""
        scored = [
            ScoredSentence("라면이 맛있어요", ["라면이"], 3, 80.0, {}),
        ]
        results = diversify_results(scored, count=5)
        assert len(results) == 1
