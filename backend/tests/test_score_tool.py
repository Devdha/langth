import pytest
from app.agents.tools.score import score_sentences, ScoredSentence
from app.api.v2.schemas import (
    GenerateRequestV2,
    TargetConfig,
    PhonemePosition,
    Language,
    DiagnosisType,
    TherapyApproach,
    CommunicativeFunction,
)


@pytest.fixture
def korean_request():
    return GenerateRequestV2(
        language=Language.KO,
        age=5,
        count=10,
        target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
        sentenceLength=4,
        diagnosis=DiagnosisType.SSD,
        therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        theme="daily",
    )


@pytest.fixture
def asd_request():
    return GenerateRequestV2(
        language=Language.KO,
        age=5,
        count=10,
        target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
        sentenceLength=4,
        diagnosis=DiagnosisType.ASD,
        therapyApproach=TherapyApproach.CORE_VOCABULARY,
        communicativeFunction=CommunicativeFunction.REQUEST,
    )


@pytest.fixture
def english_request():
    return GenerateRequestV2(
        language=Language.EN,
        age=5,
        count=10,
        target=TargetConfig(phoneme="r", position=PhonemePosition.ONSET, minOccurrences=1),
        sentenceLength=4,
        diagnosis=DiagnosisType.SSD,
        therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        theme="daily",
    )


@pytest.fixture
def english_core_vocab_request():
    return GenerateRequestV2(
        language=Language.EN,
        age=5,
        count=10,
        target=None,
        sentenceLength=4,
        diagnosis=DiagnosisType.ASD,
        therapyApproach=TherapyApproach.CORE_VOCABULARY,
    )


class TestScoreSentences:
    def test_returns_scored_sentences(self, korean_request):
        """점수가 부여된 문장 반환"""
        validated = [
            {"sentence": "라면이 너무 맛있어요", "matched_words": ["라면이"], "word_count": 4},
        ]
        results = score_sentences(validated, korean_request)

        assert len(results) == 1
        assert isinstance(results[0], ScoredSentence)
        assert results[0].score > 0

    def test_score_breakdown_included(self, korean_request):
        """점수 breakdown 포함"""
        validated = [
            {"sentence": "라면이 너무 맛있어요", "matched_words": ["라면이"], "word_count": 4},
        ]
        results = score_sentences(validated, korean_request)

        assert "frequency" in results[0].breakdown
        assert "function" in results[0].breakdown

    def test_function_score_for_asd(self, asd_request):
        """ASD 요청 시 기능 점수 가산"""
        validated = [
            {"sentence": "라면 주세요 먹고 싶어요", "matched_words": ["라면"], "word_count": 4},  # 요청 패턴
            {"sentence": "라면이 맛있어 보여요", "matched_words": ["라면이"], "word_count": 4},   # 일반 문장
        ]
        results = score_sentences(validated, asd_request)

        # 요청 패턴이 더 높은 점수
        request_score = next(r for r in results if "주세요" in r.sentence or "싶어" in r.sentence)
        general_score = next(r for r in results if "보여요" in r.sentence)
        # 요청 패턴이 기능 점수가 더 높아야 함
        assert request_score.breakdown["function"] >= general_score.breakdown["function"]

    def test_sorted_by_score(self, korean_request):
        """점수순 정렬"""
        validated = [
            {"sentence": "라면이 너무 맛있어요", "matched_words": ["라면이"], "word_count": 4},
            {"sentence": "라볶이랑 라면 먹자", "matched_words": ["라볶이랑", "라면"], "word_count": 4},
        ]
        results = score_sentences(validated, korean_request)

        # 내림차순 정렬 확인
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_en_scores_use_available_weights(self, english_request):
        """EN은 빈도/기능 제외 후 가중치 재정규화"""
        validated = [
            {"sentence": "Rory reads red books", "matched_words": ["Rory", "reads"], "word_count": 4},
        ]
        results = score_sentences(validated, english_request)

        match_bonus = 60.0  # 2 * 30
        length_fit = 100.0
        expected = round(
            (match_bonus * (0.2 / 0.3)) + (length_fit * (0.1 / 0.3)),
            2,
        )
        assert results[0].score == expected

    def test_en_core_vocab_scores_use_length_only(self, english_core_vocab_request):
        """EN core_vocabulary는 length_fit만 반영"""
        validated = [
            {"sentence": "Please help me now", "matched_words": [], "word_count": 4},
        ]
        results = score_sentences(validated, english_core_vocab_request)

        assert results[0].score == 100.0
