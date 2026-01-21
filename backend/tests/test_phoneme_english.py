import pytest
from app.services.phoneme.english import (
    get_phonemes,
    has_target_phoneme,
    find_phoneme_matches_en,
    PHONEME_MAP,
)


class TestGetPhonemes:
    def test_get_phonemes_basic(self):
        phonemes = get_phonemes("red")
        assert "R" in phonemes
        assert "EH" in phonemes
        assert "D" in phonemes

    def test_get_phonemes_stress_removed(self):
        phonemes = get_phonemes("about")
        assert all(not p[-1].isdigit() for p in phonemes if p)

    def test_get_phonemes_empty(self):
        phonemes = get_phonemes("")
        assert phonemes == []

    def test_get_phonemes_oov_word(self):
        """OOV 단어는 G2P 뉴럴넷으로 예측합니다."""
        # 'zorbax'는 CMUdict에 없는 가상의 단어
        phonemes = get_phonemes("zorbax")
        assert isinstance(phonemes, list)
        assert len(phonemes) > 0  # G2P가 음소를 생성해야 함


class TestHasTargetPhoneme:
    def test_r_sound(self):
        assert has_target_phoneme("red", "R") is True
        assert has_target_phoneme("car", "R") is True
        assert has_target_phoneme("sun", "R") is False

    def test_s_sound(self):
        assert has_target_phoneme("sun", "S") is True
        assert has_target_phoneme("bus", "S") is True
        assert has_target_phoneme("red", "S") is False

    def test_case_insensitive(self):
        assert has_target_phoneme("RED", "R") is True
        assert has_target_phoneme("Red", "R") is True


class TestFindPhonemeMatchesEn:
    def test_find_matches(self):
        result = find_phoneme_matches_en("The red car is fast", "R")
        assert "red" in result.matched_words
        assert "car" in result.matched_words
        assert result.count == 2

    def test_find_no_matches(self):
        result = find_phoneme_matches_en("The sun is hot", "R")
        assert result.matched_words == []
        assert result.count == 0

    def test_min_occurrences(self):
        result = find_phoneme_matches_en("The red ball", "R", min_occurrences=2)
        assert result.meets_minimum is False
        result = find_phoneme_matches_en("The red car runs", "R", min_occurrences=2)
        assert result.meets_minimum is True


class TestPhonemeMap:
    def test_common_phonemes_exist(self):
        assert "R" in PHONEME_MAP
        assert "L" in PHONEME_MAP
        assert "S" in PHONEME_MAP
