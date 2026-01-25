"""아동 안전 가드레일 테스트.

금칙어 필터링 기능을 테스트합니다.
"""

import pytest
from app.agents.guardrails.child_safety import filter_unsafe_sentences


class TestChildSafetyFilter:
    def test_filters_forbidden_words(self):
        """금칙어 포함 문장 필터링"""
        sentences = [
            "라면이 맛있어요",      # OK
            "술을 마시고 싶어",     # 금칙어
            "담배가 피고 싶어",     # 금칙어
            "사과를 먹고 싶어",     # OK
        ]
        filtered = filter_unsafe_sentences(sentences)

        assert "라면이 맛있어요" in filtered
        assert "사과를 먹고 싶어" in filtered
        assert len(filtered) == 2

    def test_keeps_safe_sentences(self):
        """안전한 문장 유지"""
        sentences = [
            "엄마랑 놀이터 가요",
            "아빠가 책 읽어줘요",
        ]
        filtered = filter_unsafe_sentences(sentences)

        assert len(filtered) == 2

    def test_empty_input(self):
        """빈 입력 처리"""
        filtered = filter_unsafe_sentences([])
        assert filtered == []
