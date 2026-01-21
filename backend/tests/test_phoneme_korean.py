import pytest
from app.services.phoneme.korean import (
    decompose_hangul,
    has_phoneme_at_position,
    find_phoneme_matches,
)


class TestDecomposeHangul:
    def test_decompose_basic(self):
        result = decompose_hangul("가")
        assert result == ("ㄱ", "ㅏ", "")

    def test_decompose_with_jongsung(self):
        result = decompose_hangul("강")
        assert result == ("ㄱ", "ㅏ", "ㅇ")

    def test_decompose_non_hangul(self):
        result = decompose_hangul("A")
        assert result is None

    def test_decompose_ieung_onset(self):
        result = decompose_hangul("아")
        assert result == ("ㅇ", "ㅏ", "")


class TestHasPhonemeAtPosition:
    def test_onset_match(self):
        assert has_phoneme_at_position("라면", "ㄹ", "onset") is True
        assert has_phoneme_at_position("사과", "ㄹ", "onset") is False

    def test_coda_match(self):
        assert has_phoneme_at_position("강", "ㅇ", "coda") is True
        assert has_phoneme_at_position("가", "ㅇ", "coda") is False

    def test_nucleus_match(self):
        assert has_phoneme_at_position("사과", "ㅏ", "nucleus") is True
        assert has_phoneme_at_position("수박", "ㅏ", "nucleus") is False

    def test_any_position(self):
        assert has_phoneme_at_position("라면", "ㄹ", "any") is True
        assert has_phoneme_at_position("달", "ㄹ", "any") is True

    def test_ieung_onset_excluded(self):
        assert has_phoneme_at_position("아기", "ㅇ", "onset") is False
        assert has_phoneme_at_position("강", "ㅇ", "coda") is True

    def test_ieung_any_only_coda(self):
        assert has_phoneme_at_position("강", "ㅇ", "any") is True
        assert has_phoneme_at_position("아기", "ㅇ", "any") is False


class TestFindPhonemeMatches:
    def test_find_matches_in_sentence(self):
        result = find_phoneme_matches("라면 먹고 싶어요", "ㄹ", "onset")
        assert result.matched_words == ["라면"]
        assert result.count == 1

    def test_find_multiple_matches(self):
        result = find_phoneme_matches("라면이랑 라볶이 먹자", "ㄹ", "onset")
        assert "라면이랑" in result.matched_words
        assert "라볶이" in result.matched_words
        assert result.count == 2

    def test_find_no_matches(self):
        result = find_phoneme_matches("사과 먹자", "ㄹ", "onset")
        assert result.matched_words == []
        assert result.count == 0

    def test_min_occurrences(self):
        result = find_phoneme_matches("라면 먹자", "ㄹ", "onset", min_occurrences=2)
        assert result.meets_minimum is False
        result = find_phoneme_matches("라면이랑 라볶이", "ㄹ", "onset", min_occurrences=2)
        assert result.meets_minimum is True
