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

    def test_limits_starting_word_repetition(self):
        """문장 시작어 반복 완화"""
        scored = [
            ScoredSentence("나는 사과를 좋아해요", ["사과를"], 4, 90.0, {}),
            ScoredSentence("나는 바나나를 좋아해요", ["바나나를"], 4, 89.0, {}),
            ScoredSentence("나는 딸기를 좋아해요", ["딸기를"], 4, 88.0, {}),
            ScoredSentence("너는 집에 가요", ["집에"], 4, 86.0, {}),
            ScoredSentence("우리는 공원에 가요", ["공원에"], 4, 85.0, {}),
        ]

        results = diversify_results(scored, count=3)
        starts = [r.sentence.split()[0] for r in results]
        assert len(set(starts)) >= 2

    def test_limits_repetitive_endings(self):
        """문장 종결형 반복 완화"""
        scored = [
            ScoredSentence("사과를 먹어요", ["사과를"], 3, 90.0, {}),
            ScoredSentence("바나나를 먹어요", ["바나나를"], 3, 89.0, {}),
            ScoredSentence("딸기를 먹어요", ["딸기를"], 3, 88.0, {}),
            ScoredSentence("공원에 가요", ["공원에"], 3, 87.0, {}),
        ]

        results = diversify_results(scored, count=3)
        endings = [r.sentence.split()[-1] for r in results]
        assert len(set(endings)) >= 2
