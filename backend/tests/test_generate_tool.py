"""Tests for the generate_candidates tool and prompt builder.

This module tests:
- Prompt generation for Korean and English languages
- Diagnosis-specific prompt customization (SSD, ASD, LD)
- Communicative function integration in prompts
"""

import pytest

from app.services.prompt.builder import build_generation_prompt
from app.api.v2.schemas import (
    GenerateRequestV2,
    TargetConfig,
    PhonemePosition,
    Language,
    DiagnosisType,
    TherapyApproach,
    CommunicativeFunction,
)


class TestBuildGenerationPrompt:
    """Test cases for the build_generation_prompt function."""

    def test_korean_ssd_prompt(self):
        """한국어 SSD 프롬프트 생성 테스트.

        Korean SSD prompt should include:
        - Korean language context
        - Target phoneme (ㄹ)
        - Sentence length in 어절
        - Age-appropriate guidelines
        """
        request = GenerateRequestV2(
            language=Language.KO,
            age=5,
            count=10,
            target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
            theme="daily",
        )
        prompt = build_generation_prompt(request, batch_size=30)

        assert "한국어" in prompt or "Korean" in prompt.lower()
        assert "ㄹ" in prompt
        assert "4" in prompt  # 어절
        assert "5세" in prompt or "5 years" in prompt.lower()

    def test_english_prompt(self):
        """영어 프롬프트 생성 테스트.

        English prompt should include:
        - English language context
        - Target phoneme (R)
        - Sentence specifications
        """
        request = GenerateRequestV2(
            language=Language.EN,
            age=5,
            count=10,
            target=TargetConfig(phoneme="R", position=PhonemePosition.ANY, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        )
        prompt = build_generation_prompt(request, batch_size=30)

        assert "English" in prompt or "english" in prompt.lower()
        assert "R" in prompt or "/r/" in prompt.lower()

    def test_asd_function_included(self):
        """ASD 의사소통 기능 프롬프트 테스트.

        ASD prompt with communicative function should include
        the appropriate function description.
        """
        request = GenerateRequestV2(
            language=Language.KO,
            age=5,
            count=10,
            target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.ASD,
            therapyApproach=TherapyApproach.CORE_VOCABULARY,
            communicativeFunction=CommunicativeFunction.REQUEST,
        )
        prompt = build_generation_prompt(request, batch_size=30)

        assert "요청" in prompt or "request" in prompt.lower()

    def test_prompt_includes_batch_size(self):
        """프롬프트에 배치 크기가 포함되는지 테스트."""
        request = GenerateRequestV2(
            language=Language.KO,
            age=4,
            count=5,
            target=TargetConfig(phoneme="ㅅ", position=PhonemePosition.CODA, minOccurrences=2),
            sentenceLength=3,
            diagnosis=DiagnosisType.LD,
            therapyApproach=TherapyApproach.COMPLEXITY,
        )
        prompt = build_generation_prompt(request, batch_size=15)

        assert "15" in prompt

    def test_prompt_includes_position_description(self):
        """프롬프트에 음소 위치 설명이 포함되는지 테스트."""
        request = GenerateRequestV2(
            language=Language.KO,
            age=6,
            count=10,
            target=TargetConfig(phoneme="ㄱ", position=PhonemePosition.CODA, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        )
        prompt = build_generation_prompt(request, batch_size=30)

        # Should mention coda position (종성/끝소리)
        assert "종성" in prompt or "끝소리" in prompt or "coda" in prompt.lower()

    def test_prompt_includes_theme_when_provided(self):
        """테마가 제공되면 프롬프트에 포함되는지 테스트."""
        request = GenerateRequestV2(
            language=Language.KO,
            age=5,
            count=10,
            target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ANY, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
            theme="animals",
        )
        prompt = build_generation_prompt(request, batch_size=30)

        # Should include theme description
        assert "동물" in prompt or "animal" in prompt.lower()

    def test_prompt_json_output_format(self):
        """프롬프트에 JSON 출력 형식이 포함되는지 테스트."""
        request = GenerateRequestV2(
            language=Language.KO,
            age=5,
            count=10,
            target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        )
        prompt = build_generation_prompt(request, batch_size=30)

        # New format uses "sets" for minimal_pairs/maximal_oppositions, "items" for others
        assert "sets" in prompt.lower() or "items" in prompt.lower()
        assert "json" in prompt.lower()
        assert "tokens" in prompt.lower()  # All formats now use tokens array

    def test_english_prompt_with_all_options(self):
        """모든 옵션이 포함된 영어 프롬프트 테스트."""
        request = GenerateRequestV2(
            language=Language.EN,
            age=6,
            count=8,
            target=TargetConfig(phoneme="S", position=PhonemePosition.ONSET, minOccurrences=2),
            sentenceLength=5,
            diagnosis=DiagnosisType.ASD,
            therapyApproach=TherapyApproach.CORE_VOCABULARY,
            theme="school",
            communicativeFunction=CommunicativeFunction.QUESTION,
        )
        prompt = build_generation_prompt(request, batch_size=24)

        assert "English" in prompt or "english" in prompt.lower()
        assert "S" in prompt
        assert "24" in prompt
        assert "question" in prompt.lower()
        assert "school" in prompt.lower()

    def test_prompt_includes_child_safety_warning(self):
        """프롬프트에 아동 안전 경고가 포함되는지 테스트."""
        request = GenerateRequestV2(
            language=Language.KO,
            age=5,
            count=10,
            target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET, minOccurrences=1),
            sentenceLength=4,
            diagnosis=DiagnosisType.SSD,
            therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        )
        prompt = build_generation_prompt(request, batch_size=30)

        # Should include child safety warning
        safety_keywords_ko = ["안전", "적절", "아동"]
        safety_keywords_en = ["safe", "appropriate", "child"]
        has_safety = any(kw in prompt for kw in safety_keywords_ko) or any(
            kw in prompt.lower() for kw in safety_keywords_en
        )
        assert has_safety, "Prompt should include child safety warning"
