import pytest
from app.agents.tools.validate import validate_sentences, ValidationResult
from app.api.v2.schemas import (
    GenerateRequestV2,
    TargetConfig,
    PhonemePosition,
    Language,
    DiagnosisType,
    TherapyApproach,
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
    )


@pytest.fixture
def english_request():
    return GenerateRequestV2(
        language=Language.EN,
        age=5,
        count=10,
        target=TargetConfig(phoneme="R", position=PhonemePosition.ANY, minOccurrences=1),
        sentenceLength=4,
        diagnosis=DiagnosisType.SSD,
        therapyApproach=TherapyApproach.MINIMAL_PAIRS,
    )


@pytest.fixture
def core_vocab_request():
    return GenerateRequestV2(
        language=Language.KO,
        age=5,
        count=5,
        target=None,
        sentenceLength=3,
        diagnosis=DiagnosisType.ASD,
        therapyApproach=TherapyApproach.CORE_VOCABULARY,
    )


class TestValidateSentences:
    def test_korean_valid_sentence(self, korean_request):
        """한국어 유효한 문장"""
        sentences = ["라면이 정말 너무 맛있어요"]  # 4어절, ㄹ 초성 포함
        results = validate_sentences(sentences, korean_request)

        assert len(results) == 1
        assert results[0].passed is True
        assert "라면이" in results[0].matched_words

    def test_korean_wrong_word_count(self, korean_request):
        """한국어 어절 수 불일치"""
        sentences = ["라면이 맛있어"]  # 2어절
        results = validate_sentences(sentences, korean_request)

        assert len(results) == 1
        assert results[0].passed is False
        assert "word_count" in results[0].fail_reason

    def test_korean_no_phoneme(self, korean_request):
        """한국어 타깃 음소 없음"""
        sentences = ["사과가 정말 너무 맛있어요"]  # 4어절, ㄹ 없음
        results = validate_sentences(sentences, korean_request)

        assert len(results) == 1
        assert results[0].passed is False
        assert "phoneme" in results[0].fail_reason

    def test_english_valid_sentence(self, english_request):
        """영어 유효한 문장"""
        sentences = ["The red car runs"]  # 4단어, R 포함
        results = validate_sentences(sentences, english_request)

        assert len(results) == 1
        assert results[0].passed is True

    def test_english_wrong_word_count(self, english_request):
        """영어 단어 수 불일치"""
        sentences = ["Red car"]  # 2단어
        results = validate_sentences(sentences, english_request)

        assert len(results) == 1
        assert results[0].passed is False

    def test_multiple_sentences(self, korean_request):
        """여러 문장 검증"""
        sentences = [
            "라면이 정말 너무 맛있어요",  # 유효 (4어절, ㄹ)
            "사과가 맛있어",              # 무효 (2어절, no ㄹ)
            "달리기를 정말 하고 싶어요",  # 유효 (4어절, ㄹ)
        ]
        results = validate_sentences(sentences, korean_request)

        passed = [r for r in results if r.passed]
        assert len(passed) == 2

    def test_core_vocab_requires_core_word(self, core_vocab_request):
        """핵심어휘 포함 여부 검사"""
        sentences = ["고양이가 밥을 먹어요"]  # 3어절, core word 없음
        results = validate_sentences(sentences, core_vocab_request)

        assert len(results) == 1
        assert results[0].passed is False
        assert "core_vocabulary" in results[0].fail_reason

    def test_core_vocab_with_core_word(self, core_vocab_request):
        """핵심어휘 포함 문장 통과"""
        sentences = ["이거 밥 줘"]  # 3어절, core word 포함
        results = validate_sentences(sentences, core_vocab_request)

        assert len(results) == 1
        assert results[0].passed is True
