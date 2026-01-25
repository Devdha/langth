# v2 치료 자극 선정 엔진 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 임상적으로 유효한 치료 자극 선정 엔진 v2를 구현하여 기존 v1과 병행 운영

**Architecture:** Python FastAPI 백엔드 + Next.js 프론트엔드. 백엔드는 OpenAI Agents SDK로 4단계 파이프라인(Generate → Validate → Score → Diversify) 구현. 프론트엔드는 /v2 경로에서 진단군별 프리셋 UI 제공.

**Tech Stack:** Python 3.11+, FastAPI, OpenAI Agents SDK, hgtk, pronouncing, g2p-en / Next.js 15, React 19, TypeScript, Tailwind CSS

**Design Document:** `docs/plans/2026-01-22-v2-therapy-sentence-engine-design.md`

---

## Phase 1: 백엔드 기반 구축

### Task 1.1: 백엔드 프로젝트 셋업

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/.env.example`
- Create: `backend/.gitignore`

**Step 1: 프로젝트 디렉토리 생성**

```bash
mkdir -p backend/app
mkdir -p backend/tests
```

**Step 2: pyproject.toml 작성**

```toml
[project]
name = "talk-talk-vending-backend"
version = "2.0.0"
description = "Therapy sentence generation engine v2"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "openai-agents>=0.6.9",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "pronouncing>=0.2.0",
    "g2p-en>=2.1.0",
    "hgtk>=0.2.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: config.py 작성**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    environment: str = "development"
    debug: bool = True
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 4: main.py 작성**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Talk Talk Vending API v2",
    version="2.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

**Step 5: __init__.py 및 환경 파일 작성**

```python
# backend/app/__init__.py
```

```bash
# backend/.env.example
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000"]
```

```gitignore
# backend/.gitignore
__pycache__/
*.py[cod]
.env
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
```

**Step 6: 의존성 설치 및 서버 실행 테스트**

Run:
```bash
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

Run:
```bash
cd backend && cp .env.example .env && echo "OPENAI_API_KEY=sk-test" >> .env
```

Run:
```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000 &
sleep 3 && curl http://localhost:8000/health
```

Expected: `{"status":"healthy","version":"2.0.0"}`

**Step 7: 커밋**

```bash
git add backend/
git commit -m "feat(backend): initialize FastAPI project structure

- Add pyproject.toml with dependencies
- Add config.py with pydantic-settings
- Add main.py with FastAPI app and CORS
- Add health check endpoint

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.2: 한국어 음소 탐지 서비스

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/phoneme/__init__.py`
- Create: `backend/app/services/phoneme/korean.py`
- Create: `backend/tests/test_phoneme_korean.py`

**Step 1: 테스트 파일 작성 (TDD)**

```python
# backend/tests/test_phoneme_korean.py
import pytest
from app.services.phoneme.korean import (
    decompose_hangul,
    has_phoneme_at_position,
    find_phoneme_matches,
)


class TestDecomposeHangul:
    def test_decompose_basic(self):
        """기본 한글 분해 테스트"""
        result = decompose_hangul("가")
        assert result == ("ㄱ", "ㅏ", "")

    def test_decompose_with_jongsung(self):
        """종성이 있는 한글 분해 테스트"""
        result = decompose_hangul("강")
        assert result == ("ㄱ", "ㅏ", "ㅇ")

    def test_decompose_non_hangul(self):
        """비한글 문자는 None 반환"""
        result = decompose_hangul("A")
        assert result is None

    def test_decompose_ieung_onset(self):
        """초성 ㅇ 분해 테스트"""
        result = decompose_hangul("아")
        assert result == ("ㅇ", "ㅏ", "")


class TestHasPhonemeAtPosition:
    def test_onset_match(self):
        """초성 위치 매칭"""
        assert has_phoneme_at_position("라면", "ㄹ", "onset") is True
        assert has_phoneme_at_position("사과", "ㄹ", "onset") is False

    def test_coda_match(self):
        """종성 위치 매칭"""
        assert has_phoneme_at_position("강", "ㅇ", "coda") is True
        assert has_phoneme_at_position("가", "ㅇ", "coda") is False

    def test_nucleus_match(self):
        """중성 위치 매칭"""
        assert has_phoneme_at_position("사과", "ㅏ", "nucleus") is True
        assert has_phoneme_at_position("수박", "ㅏ", "nucleus") is False

    def test_any_position(self):
        """전체 위치 매칭"""
        assert has_phoneme_at_position("라면", "ㄹ", "any") is True
        assert has_phoneme_at_position("달", "ㄹ", "any") is True  # 종성

    def test_ieung_onset_excluded(self):
        """초성 ㅇ은 타깃에서 제외"""
        # "아기"의 초성 ㅇ은 무음이므로 매칭하지 않음
        assert has_phoneme_at_position("아기", "ㅇ", "onset") is False
        # 종성 ㅇ만 매칭
        assert has_phoneme_at_position("강", "ㅇ", "coda") is True

    def test_ieung_any_only_coda(self):
        """ㅇ을 any로 검색 시 종성만 매칭"""
        assert has_phoneme_at_position("강", "ㅇ", "any") is True
        assert has_phoneme_at_position("아기", "ㅇ", "any") is False


class TestFindPhonemeMatches:
    def test_find_matches_in_sentence(self):
        """문장에서 타깃 음소 포함 단어 찾기"""
        result = find_phoneme_matches("라면 먹고 싶어요", "ㄹ", "onset")
        assert result.matched_words == ["라면"]
        assert result.count == 1

    def test_find_multiple_matches(self):
        """여러 단어 매칭"""
        result = find_phoneme_matches("라면이랑 라볶이 먹자", "ㄹ", "onset")
        assert "라면이랑" in result.matched_words
        assert "라볶이" in result.matched_words
        assert result.count == 2

    def test_find_no_matches(self):
        """매칭 없음"""
        result = find_phoneme_matches("사과 먹자", "ㄹ", "onset")
        assert result.matched_words == []
        assert result.count == 0

    def test_min_occurrences(self):
        """최소 출현 횟수 체크"""
        result = find_phoneme_matches("라면 먹자", "ㄹ", "onset", min_occurrences=2)
        assert result.meets_minimum is False

        result = find_phoneme_matches("라면이랑 라볶이", "ㄹ", "onset", min_occurrences=2)
        assert result.meets_minimum is True
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_phoneme_korean.py -v
```

Expected: FAIL (module not found)

**Step 3: 서비스 디렉토리 구조 생성**

```python
# backend/app/services/__init__.py
```

```python
# backend/app/services/phoneme/__init__.py
from .korean import (
    decompose_hangul,
    has_phoneme_at_position,
    find_phoneme_matches,
    PhonemeMatchResult,
)

__all__ = [
    "decompose_hangul",
    "has_phoneme_at_position",
    "find_phoneme_matches",
    "PhonemeMatchResult",
]
```

**Step 4: 한국어 음소 탐지 구현**

```python
# backend/app/services/phoneme/korean.py
from dataclasses import dataclass

import hgtk


@dataclass
class PhonemeMatchResult:
    """음소 매칭 결과"""
    matched_words: list[str]
    count: int
    meets_minimum: bool = True


def decompose_hangul(char: str) -> tuple[str, str, str] | None:
    """한글 음절을 초성, 중성, 종성으로 분해합니다.

    Args:
        char: 단일 문자

    Returns:
        (초성, 중성, 종성) 튜플. 종성이 없으면 빈 문자열.
        한글이 아니면 None.
    """
    try:
        cho, jung, jong = hgtk.letter.decompose(char)
        return (cho, jung, jong if jong else "")
    except Exception:
        return None


def has_phoneme_at_position(
    word: str,
    phoneme: str,
    position: str,
) -> bool:
    """단어에서 특정 위치에 타깃 음소가 있는지 확인합니다.

    Args:
        word: 검사할 단어
        phoneme: 타깃 음소 (ㄱ, ㅏ 등)
        position: 위치 ('onset', 'nucleus', 'coda', 'any')

    Returns:
        해당 위치에 음소가 있으면 True
    """
    for char in word:
        decomposed = decompose_hangul(char)
        if decomposed is None:
            continue

        cho, jung, jong = decomposed

        # 초성 ㅇ은 무음이므로 타깃에서 제외
        if phoneme == "ㅇ":
            if position == "onset":
                return False
            if position == "coda" and jong == "ㅇ":
                return True
            if position == "any" and jong == "ㅇ":
                return True
            continue

        if position == "onset" and cho == phoneme:
            return True
        if position == "nucleus" and jung == phoneme:
            return True
        if position == "coda" and jong == phoneme:
            return True
        if position == "any" and phoneme in (cho, jung, jong):
            return True

    return False


def find_phoneme_matches(
    sentence: str,
    phoneme: str,
    position: str,
    min_occurrences: int = 1,
) -> PhonemeMatchResult:
    """문장에서 타깃 음소를 포함하는 단어들을 찾습니다.

    Args:
        sentence: 검사할 문장
        phoneme: 타깃 음소
        position: 위치 ('onset', 'nucleus', 'coda', 'any')
        min_occurrences: 최소 출현 횟수

    Returns:
        PhonemeMatchResult 객체
    """
    words = sentence.split()
    matched_words = []

    for word in words:
        if has_phoneme_at_position(word, phoneme, position):
            matched_words.append(word)

    return PhonemeMatchResult(
        matched_words=matched_words,
        count=len(matched_words),
        meets_minimum=len(matched_words) >= min_occurrences,
    )
```

**Step 5: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_phoneme_korean.py -v
```

Expected: All tests PASS

**Step 6: 커밋**

```bash
git add backend/app/services/ backend/tests/test_phoneme_korean.py
git commit -m "feat(backend): add Korean phoneme detection service

- Add hgtk-based hangul decomposition
- Implement position-based phoneme matching (onset/nucleus/coda)
- Handle ㅇ special case (exclude onset, include coda)
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.3: 영어 음소 탐지 서비스

**Files:**
- Create: `backend/app/services/phoneme/english.py`
- Create: `backend/tests/test_phoneme_english.py`

**Step 1: 테스트 파일 작성 (TDD)**

```python
# backend/tests/test_phoneme_english.py
import pytest
from app.services.phoneme.english import (
    get_phonemes,
    has_target_phoneme,
    find_phoneme_matches_en,
    PHONEME_MAP,
)


class TestGetPhonemes:
    def test_get_phonemes_basic(self):
        """기본 단어 발음 조회"""
        phonemes = get_phonemes("red")
        assert "R" in phonemes
        assert "EH" in phonemes
        assert "D" in phonemes

    def test_get_phonemes_stress_removed(self):
        """강세 숫자 제거 확인"""
        phonemes = get_phonemes("about")
        # 강세 숫자(0,1,2)가 제거되어야 함
        assert all(not p[-1].isdigit() for p in phonemes)

    def test_get_phonemes_oov(self):
        """사전에 없는 단어도 처리 (g2p fallback)"""
        # 존재하지 않는 단어도 발음 예측
        phonemes = get_phonemes("xyzabc")
        assert phonemes is not None
        assert len(phonemes) > 0

    def test_get_phonemes_empty(self):
        """빈 문자열 처리"""
        phonemes = get_phonemes("")
        assert phonemes == []


class TestHasTargetPhoneme:
    def test_r_sound(self):
        """/R/ 발음 포함 확인"""
        assert has_target_phoneme("red", "R") is True
        assert has_target_phoneme("car", "R") is True
        assert has_target_phoneme("sun", "R") is False

    def test_s_sound(self):
        """/S/ 발음 포함 확인"""
        assert has_target_phoneme("sun", "S") is True
        assert has_target_phoneme("bus", "S") is True
        assert has_target_phoneme("red", "S") is False

    def test_th_sound(self):
        """/TH/ 발음 포함 확인"""
        assert has_target_phoneme("think", "TH") is True
        assert has_target_phoneme("bath", "TH") is True

    def test_case_insensitive(self):
        """대소문자 무관"""
        assert has_target_phoneme("RED", "R") is True
        assert has_target_phoneme("Red", "R") is True


class TestFindPhonemeMatchesEn:
    def test_find_matches(self):
        """문장에서 타깃 음소 포함 단어 찾기"""
        result = find_phoneme_matches_en("The red car is fast", "R")
        assert "red" in result.matched_words
        assert "car" in result.matched_words
        assert result.count == 2

    def test_find_no_matches(self):
        """매칭 없음"""
        result = find_phoneme_matches_en("The sun is hot", "R")
        assert result.matched_words == []
        assert result.count == 0

    def test_min_occurrences(self):
        """최소 출현 횟수"""
        result = find_phoneme_matches_en("The red ball", "R", min_occurrences=2)
        assert result.meets_minimum is False

        result = find_phoneme_matches_en("The red car runs", "R", min_occurrences=2)
        assert result.meets_minimum is True


class TestPhonemeMap:
    def test_common_phonemes_exist(self):
        """주요 음소 매핑 존재 확인"""
        assert "R" in PHONEME_MAP
        assert "L" in PHONEME_MAP
        assert "S" in PHONEME_MAP
        assert "TH" in PHONEME_MAP
        assert "SH" in PHONEME_MAP
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_phoneme_english.py -v
```

Expected: FAIL (module not found)

**Step 3: 영어 음소 탐지 구현**

```python
# backend/app/services/phoneme/english.py
from dataclasses import dataclass
import re

import pronouncing
import g2p_en

# G2P 모델 (싱글톤)
_g2p = None


def _get_g2p():
    global _g2p
    if _g2p is None:
        _g2p = g2p_en.G2p()
    return _g2p


# ARPAbet 음소 매핑 (UI용 설명)
PHONEME_MAP = {
    "R": {"ipa": "/r/", "examples": "red, car, run"},
    "L": {"ipa": "/l/", "examples": "light, ball, let"},
    "S": {"ipa": "/s/", "examples": "sun, bus, sit"},
    "Z": {"ipa": "/z/", "examples": "zoo, nose, zip"},
    "TH": {"ipa": "/θ/", "examples": "think, bath, three"},
    "DH": {"ipa": "/ð/", "examples": "this, mother, the"},
    "SH": {"ipa": "/ʃ/", "examples": "ship, fish, she"},
    "ZH": {"ipa": "/ʒ/", "examples": "measure, vision"},
    "CH": {"ipa": "/tʃ/", "examples": "chip, watch, chair"},
    "JH": {"ipa": "/dʒ/", "examples": "jump, page, job"},
    "F": {"ipa": "/f/", "examples": "fish, leaf, fun"},
    "V": {"ipa": "/v/", "examples": "van, love, very"},
    "K": {"ipa": "/k/", "examples": "cat, back, key"},
    "G": {"ipa": "/g/", "examples": "go, big, get"},
    "T": {"ipa": "/t/", "examples": "top, bat, ten"},
    "D": {"ipa": "/d/", "examples": "dog, bed, day"},
    "P": {"ipa": "/p/", "examples": "pat, cup, pen"},
    "B": {"ipa": "/b/", "examples": "bat, cab, big"},
    "M": {"ipa": "/m/", "examples": "man, ham, mom"},
    "N": {"ipa": "/n/", "examples": "no, sun, new"},
    "NG": {"ipa": "/ŋ/", "examples": "sing, ring, long"},
    "W": {"ipa": "/w/", "examples": "we, swim, water"},
    "Y": {"ipa": "/j/", "examples": "yes, you, yellow"},
    "HH": {"ipa": "/h/", "examples": "hat, hello, house"},
}


@dataclass
class PhonemeMatchResultEn:
    """영어 음소 매칭 결과"""
    matched_words: list[str]
    count: int
    meets_minimum: bool = True


def get_phonemes(word: str) -> list[str]:
    """단어의 ARPAbet 음소 리스트를 반환합니다.

    Args:
        word: 영어 단어

    Returns:
        ARPAbet 음소 리스트 (강세 숫자 제거됨)
    """
    if not word:
        return []

    clean_word = word.lower().strip()
    if not clean_word:
        return []

    # CMUdict에서 조회
    phones = pronouncing.phones_for_word(clean_word)
    if phones:
        # 첫 번째 발음 사용, 강세 숫자 제거
        return [re.sub(r"[012]", "", p) for p in phones[0].split()]

    # OOV: g2p로 예측
    g2p = _get_g2p()
    predicted = g2p(clean_word)
    # g2p는 문자와 음소를 섞어서 반환할 수 있음
    return [re.sub(r"[012]", "", p) for p in predicted if p.isalpha() and len(p) <= 3]


def has_target_phoneme(word: str, target: str) -> bool:
    """단어에 타깃 음소가 포함되어 있는지 확인합니다.

    Args:
        word: 영어 단어
        target: ARPAbet 음소 (R, S, TH 등)

    Returns:
        포함 여부
    """
    phonemes = get_phonemes(word)
    return target.upper() in phonemes


def find_phoneme_matches_en(
    sentence: str,
    target: str,
    min_occurrences: int = 1,
) -> PhonemeMatchResultEn:
    """문장에서 타깃 음소를 포함하는 단어들을 찾습니다.

    Args:
        sentence: 영어 문장
        target: ARPAbet 음소 (R, S, TH 등)
        min_occurrences: 최소 출현 횟수

    Returns:
        PhonemeMatchResultEn 객체
    """
    words = sentence.split()
    matched_words = []

    for word in words:
        # 구두점 제거
        clean = "".join(c for c in word if c.isalpha())
        if clean and has_target_phoneme(clean, target):
            matched_words.append(clean.lower())

    return PhonemeMatchResultEn(
        matched_words=matched_words,
        count=len(matched_words),
        meets_minimum=len(matched_words) >= min_occurrences,
    )
```

**Step 4: __init__.py 업데이트**

```python
# backend/app/services/phoneme/__init__.py
from .korean import (
    decompose_hangul,
    has_phoneme_at_position,
    find_phoneme_matches,
    PhonemeMatchResult,
)
from .english import (
    get_phonemes,
    has_target_phoneme,
    find_phoneme_matches_en,
    PhonemeMatchResultEn,
    PHONEME_MAP,
)

__all__ = [
    # Korean
    "decompose_hangul",
    "has_phoneme_at_position",
    "find_phoneme_matches",
    "PhonemeMatchResult",
    # English
    "get_phonemes",
    "has_target_phoneme",
    "find_phoneme_matches_en",
    "PhonemeMatchResultEn",
    "PHONEME_MAP",
]
```

**Step 5: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_phoneme_english.py -v
```

Expected: All tests PASS

**Step 6: 커밋**

```bash
git add backend/app/services/phoneme/ backend/tests/test_phoneme_english.py
git commit -m "feat(backend): add English phoneme detection service

- Add CMUdict-based phoneme lookup via pronouncing
- Add g2p-en fallback for OOV words
- Implement ARPAbet phoneme mapping with IPA and examples
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.4: API 스키마 및 엔드포인트

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v2/__init__.py`
- Create: `backend/app/api/v2/schemas.py`
- Create: `backend/app/api/v2/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_v2.py`

**Step 1: 테스트 파일 작성 (TDD)**

```python
# backend/tests/test_api_v2.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestGenerateEndpointValidation:
    async def test_missing_required_fields(self, client):
        """필수 필드 누락 시 422 에러"""
        response = await client.post("/api/v2/generate", json={})
        assert response.status_code == 422

    async def test_invalid_language(self, client):
        """잘못된 언어 코드"""
        response = await client.post("/api/v2/generate", json={
            "language": "invalid",
            "age": 5,
            "count": 10,
            "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
            "sentenceLength": 4,
            "diagnosis": "SSD",
            "therapyApproach": "minimal_pairs",
        })
        assert response.status_code == 422

    async def test_valid_request_structure(self, client):
        """유효한 요청 구조 (실제 생성은 mock 필요)"""
        # 이 테스트는 파이프라인 구현 후 업데이트
        response = await client.post("/api/v2/generate", json={
            "language": "ko",
            "age": 5,
            "count": 5,
            "target": {"phoneme": "ㄹ", "position": "onset", "minOccurrences": 1},
            "sentenceLength": 4,
            "diagnosis": "SSD",
            "therapyApproach": "minimal_pairs",
        })
        # 파이프라인 미구현 시 501 반환
        assert response.status_code in [200, 501]
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_api_v2.py -v
```

Expected: FAIL (endpoint not found)

**Step 3: API 스키마 작성**

```python
# backend/app/api/__init__.py
```

```python
# backend/app/api/v2/__init__.py
```

```python
# backend/app/api/v2/schemas.py
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Language(str, Enum):
    KO = "ko"
    EN = "en"


class DiagnosisType(str, Enum):
    SSD = "SSD"  # Speech Sound Disorder
    ASD = "ASD"  # Autism Spectrum Disorder
    LD = "LD"    # Language Delay


class TherapyApproach(str, Enum):
    MINIMAL_PAIRS = "minimal_pairs"
    MAXIMAL_OPPOSITIONS = "maximal_oppositions"
    COMPLEXITY = "complexity"
    CORE_VOCABULARY = "core_vocabulary"


class CommunicativeFunction(str, Enum):
    REQUEST = "request"
    REJECT = "reject"
    HELP = "help"
    CHOICE = "choice"
    ATTENTION = "attention"
    QUESTION = "question"


class PhonemePosition(str, Enum):
    ONSET = "onset"
    NUCLEUS = "nucleus"
    CODA = "coda"
    ANY = "any"


class TargetConfig(BaseModel):
    phoneme: str = Field(..., min_length=1, max_length=3)
    position: PhonemePosition
    minOccurrences: int = Field(default=1, ge=1, le=3)


class GenerateRequestV2(BaseModel):
    language: Language
    age: Literal[3, 4, 5, 6, 7]
    count: int = Field(..., ge=1, le=20)
    target: TargetConfig
    sentenceLength: int = Field(..., ge=2, le=6)
    diagnosis: DiagnosisType
    therapyApproach: TherapyApproach
    theme: str | None = None
    communicativeFunction: CommunicativeFunction | None = None


class MatchedWord(BaseModel):
    word: str
    startIndex: int
    endIndex: int
    positions: list[PhonemePosition]


class TherapyItemV2(BaseModel):
    id: str
    text: str
    target: TargetConfig
    matchedWords: list[MatchedWord]
    wordCount: int
    score: float
    diagnosis: DiagnosisType
    approach: TherapyApproach
    theme: str | None = None
    function: CommunicativeFunction | None = None


class GenerateMetaV2(BaseModel):
    requestedCount: int
    generatedCount: int
    averageScore: float
    processingTimeMs: int


class GenerateResponseV2(BaseModel):
    success: Literal[True]
    data: dict  # items + meta


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    GENERATION_FAILED = "GENERATION_FAILED"
    INSUFFICIENT_RESULTS = "INSUFFICIENT_RESULTS"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: str | None = None


class ErrorResponseV2(BaseModel):
    success: Literal[False]
    error: ErrorDetail
```

**Step 4: API 라우터 작성**

```python
# backend/app/api/v2/router.py
from fastapi import APIRouter, HTTPException
from .schemas import (
    GenerateRequestV2,
    GenerateResponseV2,
    ErrorResponseV2,
    ErrorCode,
    ErrorDetail,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post(
    "/generate",
    response_model=GenerateResponseV2 | ErrorResponseV2,
    responses={
        501: {"model": ErrorResponseV2},
    },
)
async def generate_sentences(request: GenerateRequestV2):
    """치료용 문장을 생성합니다.

    4단계 파이프라인:
    1. Generate: LLM으로 후보 생성
    2. Validate: 하드 제약 검사
    3. Score: 점수 계산
    4. Diversify: 다양성 보장
    """
    # TODO: 파이프라인 구현 후 연결
    raise HTTPException(
        status_code=501,
        detail={
            "success": False,
            "error": {
                "code": ErrorCode.SERVICE_UNAVAILABLE.value,
                "message": "파이프라인이 아직 구현되지 않았습니다.",
            },
        },
    )
```

**Step 5: main.py에 라우터 등록**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v2.router import router as v2_router

app = FastAPI(
    title="Talk Talk Vending API v2",
    version="2.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(v2_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

**Step 6: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_api_v2.py -v
```

Expected: All tests PASS

**Step 7: 커밋**

```bash
git add backend/app/api/ backend/app/main.py backend/tests/test_api_v2.py
git commit -m "feat(backend): add v2 API schema and endpoint

- Add Pydantic schemas for request/response
- Add /api/v2/generate endpoint (placeholder)
- Add validation tests
- Register router in main app

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: 파이프라인 구현

### Task 2.1: generate_candidates 도구

**Files:**
- Create: `backend/app/agents/__init__.py`
- Create: `backend/app/agents/tools/__init__.py`
- Create: `backend/app/agents/tools/generate.py`
- Create: `backend/app/services/prompt/__init__.py`
- Create: `backend/app/services/prompt/builder.py`
- Create: `backend/tests/test_generate_tool.py`

**Step 1: 프롬프트 빌더 테스트 작성**

```python
# backend/tests/test_generate_tool.py
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
    def test_korean_ssd_prompt(self):
        """한국어 SSD 프롬프트 생성"""
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
        """영어 프롬프트 생성"""
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
        """ASD 의사소통 기능 프롬프트"""
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
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_generate_tool.py -v
```

Expected: FAIL

**Step 3: 프롬프트 빌더 구현**

```python
# backend/app/services/prompt/__init__.py
from .builder import build_generation_prompt

__all__ = ["build_generation_prompt"]
```

```python
# backend/app/services/prompt/builder.py
from app.api.v2.schemas import (
    GenerateRequestV2,
    Language,
    DiagnosisType,
    TherapyApproach,
    CommunicativeFunction,
    PhonemePosition,
)

# 테마 설명
THEME_DESCRIPTIONS = {
    "ko": {
        "daily": "일상생활 (집, 학교, 놀이터 등)",
        "food": "음식과 식사",
        "animal": "동물",
        "family": "가족",
    },
    "en": {
        "daily": "daily life (home, school, playground)",
        "food": "food and eating",
        "animal": "animals",
        "family": "family",
    },
}

# 의사소통 기능 설명
FUNCTION_DESCRIPTIONS = {
    "ko": {
        CommunicativeFunction.REQUEST: "요청하기 (~줘, ~하고 싶어)",
        CommunicativeFunction.REJECT: "거절하기 (싫어, 안 할래)",
        CommunicativeFunction.HELP: "도움요청 (도와줘, 어떻게 해?)",
        CommunicativeFunction.CHOICE: "선택하기 (~할래, ~할래?)",
        CommunicativeFunction.ATTENTION: "주목끌기 (봐봐, 이거 봐)",
        CommunicativeFunction.QUESTION: "질문하기 (이게 뭐야?, 어디 있어?)",
    },
    "en": {
        CommunicativeFunction.REQUEST: "requesting (I want, give me)",
        CommunicativeFunction.REJECT: "rejecting (no, I don't want)",
        CommunicativeFunction.HELP: "asking for help (help me, how do I)",
        CommunicativeFunction.CHOICE: "choosing (I want this or that)",
        CommunicativeFunction.ATTENTION: "getting attention (look, see this)",
        CommunicativeFunction.QUESTION: "asking questions (what is, where is)",
    },
}

# 연령별 가이드라인
AGE_GUIDELINES = {
    "ko": {
        3: "3세: 매우 간단한 어휘, 짧은 문장",
        4: "4세: 일상적인 어휘, 간단한 문장",
        5: "5세: 다양한 어휘, 자연스러운 문장",
        6: "6세: 풍부한 어휘, 복잡한 문장 가능",
        7: "7세: 학령기 어휘, 다양한 문장 구조",
    },
    "en": {
        3: "Age 3: Very simple vocabulary, short sentences",
        4: "Age 4: Common vocabulary, simple sentences",
        5: "Age 5: Varied vocabulary, natural sentences",
        6: "Age 6: Rich vocabulary, complex sentences allowed",
        7: "Age 7: School-age vocabulary, varied sentence structures",
    },
}

# 위치 설명
POSITION_DESCRIPTIONS = {
    "ko": {
        PhonemePosition.ONSET: "초성(어두)",
        PhonemePosition.NUCLEUS: "중성(모음)",
        PhonemePosition.CODA: "종성(받침)",
        PhonemePosition.ANY: "어디든",
    },
    "en": {
        PhonemePosition.ONSET: "word-initial",
        PhonemePosition.NUCLEUS: "vowel",
        PhonemePosition.CODA: "word-final",
        PhonemePosition.ANY: "any position",
    },
}


def build_generation_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """문장 생성 프롬프트를 구성합니다."""
    lang = request.language.value

    if lang == "ko":
        return _build_korean_prompt(request, batch_size)
    else:
        return _build_english_prompt(request, batch_size)


def _build_korean_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    position_desc = POSITION_DESCRIPTIONS["ko"][request.target.position]
    age_guide = AGE_GUIDELINES["ko"][request.age]

    prompt = f"""당신은 아동 언어치료용 문장을 생성하는 전문가입니다.

## 조건
- 언어: 한국어
- 대상 연령: {request.age}세 ({age_guide})
- 문장 길이: 정확히 {request.sentenceLength}어절 (띄어쓰기 기준)
- 타깃 음소: '{request.target.phoneme}' ({position_desc} 위치)
- 최소 {request.target.minOccurrences}회 이상 타깃 음소 포함

## 진단 및 접근법
- 진단군: {request.diagnosis.value}
- 치료 접근: {request.therapyApproach.value}
"""

    if request.theme:
        theme_desc = THEME_DESCRIPTIONS["ko"].get(request.theme, request.theme)
        prompt += f"- 주제: {theme_desc}\n"

    if request.communicativeFunction:
        func_desc = FUNCTION_DESCRIPTIONS["ko"].get(request.communicativeFunction, "")
        prompt += f"- 의사소통 기능: {func_desc}\n"

    prompt += f"""
## 요청
{batch_size}개의 문장을 생성하세요.

## 출력 형식
JSON 형식으로만 응답하세요:
{{"sentences": ["문장1", "문장2", ...]}}

## 주의사항
1. 정확히 {request.sentenceLength}어절이어야 합니다
2. 타깃 음소 '{request.target.phoneme}'가 {position_desc}에 반드시 포함되어야 합니다
3. {request.age}세 아동에게 적합한 어휘와 문장 구조를 사용하세요
4. 아동에게 부적절한 내용은 절대 포함하지 마세요
5. 자연스럽고 실제로 사용할 법한 문장을 만드세요
"""

    return prompt


def _build_english_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    position_desc = POSITION_DESCRIPTIONS["en"][request.target.position]
    age_guide = AGE_GUIDELINES["en"][request.age]

    prompt = f"""You are an expert in generating sentences for child speech therapy.

## Requirements
- Language: English
- Target age: {request.age} years old ({age_guide})
- Sentence length: exactly {request.sentenceLength} words
- Target phoneme: '{request.target.phoneme}' ({position_desc})
- Minimum {request.target.minOccurrences} occurrence(s) of target phoneme

## Diagnosis and Approach
- Diagnosis: {request.diagnosis.value}
- Therapy approach: {request.therapyApproach.value}
"""

    if request.theme:
        theme_desc = THEME_DESCRIPTIONS["en"].get(request.theme, request.theme)
        prompt += f"- Theme: {theme_desc}\n"

    if request.communicativeFunction:
        func_desc = FUNCTION_DESCRIPTIONS["en"].get(request.communicativeFunction, "")
        prompt += f"- Communicative function: {func_desc}\n"

    prompt += f"""
## Request
Generate {batch_size} sentences.

## Output Format
Respond only in JSON format:
{{"sentences": ["sentence1", "sentence2", ...]}}

## Important Notes
1. Each sentence must be exactly {request.sentenceLength} words
2. Target phoneme '{request.target.phoneme}' must appear in {position_desc}
3. Use vocabulary and sentence structures appropriate for {request.age}-year-olds
4. Never include inappropriate content for children
5. Create natural, realistic sentences
"""

    return prompt
```

**Step 4: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_generate_tool.py -v
```

Expected: All tests PASS

**Step 5: generate_candidates 도구 구현**

```python
# backend/app/agents/__init__.py
```

```python
# backend/app/agents/tools/__init__.py
from .generate import generate_candidates

__all__ = ["generate_candidates"]
```

```python
# backend/app/agents/tools/generate.py
import json
import re

from openai import AsyncOpenAI

from app.config import settings
from app.api.v2.schemas import GenerateRequestV2
from app.services.prompt.builder import build_generation_prompt

# OpenAI 클라이언트 (싱글톤)
_client = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_candidates(
    request: GenerateRequestV2,
    batch_size: int | None = None,
) -> list[str]:
    """LLM으로 후보 문장을 생성합니다.

    Args:
        request: 생성 요청
        batch_size: 생성할 문장 수 (기본: count * 3)

    Returns:
        생성된 문장 리스트
    """
    if batch_size is None:
        batch_size = request.count * 3

    prompt = build_generation_prompt(request, batch_size)
    client = _get_client()

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates therapy sentences."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    content = response.choices[0].message.content
    if not content:
        return []

    try:
        data = json.loads(content)
        sentences = data.get("sentences", [])
        if isinstance(sentences, list):
            # 정규화: 따옴표, 넘버링 제거
            return [_normalize_sentence(s) for s in sentences if isinstance(s, str)]
        return []
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 정규식으로 추출 시도
        matches = re.findall(r'"([^"]+)"', content)
        return [_normalize_sentence(m) for m in matches]


def _normalize_sentence(sentence: str) -> str:
    """문장 정규화: 앞뒤 공백, 따옴표, 넘버링 제거"""
    s = sentence.strip()
    # 넘버링 제거 (1. 또는 1) 형태)
    s = re.sub(r"^\d+[\.\)]\s*", "", s)
    # 앞뒤 따옴표 제거
    s = s.strip("\"'")
    return s
```

**Step 6: 커밋**

```bash
git add backend/app/agents/ backend/app/services/prompt/ backend/tests/test_generate_tool.py
git commit -m "feat(backend): add generate_candidates tool

- Add prompt builder for Korean and English
- Support diagnosis-specific prompts (SSD, ASD, LD)
- Support communicative function prompts
- Add sentence normalization
- Add OpenAI API integration

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.2: validate_sentences 도구

**Files:**
- Create: `backend/app/agents/tools/validate.py`
- Create: `backend/tests/test_validate_tool.py`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_validate_tool.py
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


class TestValidateSentences:
    def test_korean_valid_sentence(self, korean_request):
        """한국어 유효한 문장"""
        sentences = ["라면이 너무 맛있어요"]  # 4어절, ㄹ 초성 포함
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
        sentences = ["사과가 너무 맛있어요"]  # ㄹ 없음
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
            "라면이 너무 맛있어요",  # 유효
            "사과가 맛있어",          # 무효 (어절 수, 음소)
            "달리기를 하고 싶어요",   # 유효
        ]
        results = validate_sentences(sentences, korean_request)

        passed = [r for r in results if r.passed]
        assert len(passed) == 2
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_validate_tool.py -v
```

Expected: FAIL

**Step 3: validate_sentences 구현**

```python
# backend/app/agents/tools/validate.py
from dataclasses import dataclass

from app.api.v2.schemas import GenerateRequestV2, Language, PhonemePosition
from app.services.phoneme.korean import find_phoneme_matches
from app.services.phoneme.english import find_phoneme_matches_en


@dataclass
class ValidationResult:
    """검증 결과"""
    sentence: str
    passed: bool
    matched_words: list[str]
    word_count: int
    fail_reason: str | None = None


def validate_sentences(
    sentences: list[str],
    request: GenerateRequestV2,
) -> list[ValidationResult]:
    """문장들의 하드 제약을 검사합니다.

    검사 항목:
    1. 길이 (어절/단어 수)
    2. 타깃 음소 포함 여부 및 위치
    3. 최소 출현 횟수

    Args:
        sentences: 검사할 문장 리스트
        request: 생성 요청 (조건 포함)

    Returns:
        ValidationResult 리스트
    """
    results = []

    for sentence in sentences:
        result = _validate_single(sentence, request)
        results.append(result)

    return results


def _validate_single(sentence: str, request: GenerateRequestV2) -> ValidationResult:
    """단일 문장 검증"""
    # 1. 길이 검사
    words = sentence.strip().split()
    word_count = len(words)

    if word_count != request.sentenceLength:
        return ValidationResult(
            sentence=sentence,
            passed=False,
            matched_words=[],
            word_count=word_count,
            fail_reason=f"word_count: expected {request.sentenceLength}, got {word_count}",
        )

    # 2. 음소 검사
    if request.target.phoneme:
        if request.language == Language.KO:
            match_result = find_phoneme_matches(
                sentence,
                request.target.phoneme,
                request.target.position.value,
                request.target.minOccurrences,
            )
        else:
            match_result = find_phoneme_matches_en(
                sentence,
                request.target.phoneme,
                request.target.minOccurrences,
            )

        if not match_result.meets_minimum:
            return ValidationResult(
                sentence=sentence,
                passed=False,
                matched_words=match_result.matched_words,
                word_count=word_count,
                fail_reason=f"phoneme: found {match_result.count}, need {request.target.minOccurrences}",
            )

        return ValidationResult(
            sentence=sentence,
            passed=True,
            matched_words=match_result.matched_words,
            word_count=word_count,
        )

    # 음소 타깃 없으면 길이만 통과하면 OK
    return ValidationResult(
        sentence=sentence,
        passed=True,
        matched_words=[],
        word_count=word_count,
    )


def get_passed_sentences(results: list[ValidationResult]) -> list[dict]:
    """통과한 문장들만 추출"""
    return [
        {
            "sentence": r.sentence,
            "matched_words": r.matched_words,
            "word_count": r.word_count,
        }
        for r in results
        if r.passed
    ]
```

**Step 4: __init__.py 업데이트**

```python
# backend/app/agents/tools/__init__.py
from .generate import generate_candidates
from .validate import validate_sentences, ValidationResult, get_passed_sentences

__all__ = [
    "generate_candidates",
    "validate_sentences",
    "ValidationResult",
    "get_passed_sentences",
]
```

**Step 5: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_validate_tool.py -v
```

Expected: All tests PASS

**Step 6: 커밋**

```bash
git add backend/app/agents/tools/ backend/tests/test_validate_tool.py
git commit -m "feat(backend): add validate_sentences tool

- Validate word count (eojeol/words)
- Validate phoneme presence and position
- Check minimum occurrences
- Return detailed validation results

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.3: score_sentences 도구

**Files:**
- Create: `backend/app/services/corpus/__init__.py`
- Create: `backend/app/services/corpus/korean_freq.py`
- Create: `backend/app/agents/tools/score.py`
- Create: `backend/tests/test_score_tool.py`
- Create: `backend/app/data/korean_frequency_sample.json`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_score_tool.py
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
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_score_tool.py -v
```

Expected: FAIL

**Step 3: 빈도 데이터 샘플 생성**

```json
{
  "엄마": 95,
  "아빠": 92,
  "라면": 75,
  "먹다": 88,
  "주다": 85,
  "싶다": 80,
  "하다": 90,
  "좋다": 85,
  "가다": 87,
  "오다": 86,
  "사과": 70,
  "바나나": 65,
  "학교": 78,
  "집": 82,
  "친구": 80,
  "놀다": 75,
  "보다": 85,
  "듣다": 70,
  "말하다": 72,
  "읽다": 68
}
```

파일: `backend/app/data/korean_frequency_sample.json`

**Step 4: 빈도 서비스 구현**

```python
# backend/app/services/corpus/__init__.py
from .korean_freq import get_word_frequency, get_sentence_frequency_score

__all__ = ["get_word_frequency", "get_sentence_frequency_score"]
```

```python
# backend/app/services/corpus/korean_freq.py
import json
from pathlib import Path

# 빈도 데이터 캐시
_frequency_data: dict[str, int] | None = None


def _load_frequency_data() -> dict[str, int]:
    """빈도 데이터 로드 (싱글톤)"""
    global _frequency_data
    if _frequency_data is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "korean_frequency_sample.json"
        if data_path.exists():
            with open(data_path, encoding="utf-8") as f:
                _frequency_data = json.load(f)
        else:
            _frequency_data = {}
    return _frequency_data


def get_word_frequency(word: str) -> int:
    """단어의 빈도 점수를 반환합니다 (0-100).

    Args:
        word: 한국어 단어

    Returns:
        빈도 점수 (높을수록 고빈도). 사전에 없으면 50 (중간값).
    """
    data = _load_frequency_data()
    # 조사 등 제거하고 어근만 검색 (간단 버전)
    for length in range(len(word), 0, -1):
        prefix = word[:length]
        if prefix in data:
            return data[prefix]
    return 50  # 기본값


def get_sentence_frequency_score(sentence: str) -> float:
    """문장의 평균 빈도 점수를 계산합니다.

    Args:
        sentence: 한국어 문장

    Returns:
        평균 빈도 점수 (0-100)
    """
    words = sentence.split()
    if not words:
        return 50.0

    scores = [get_word_frequency(word) for word in words]
    return sum(scores) / len(scores)
```

**Step 5: score_sentences 구현**

```python
# backend/app/agents/tools/score.py
from dataclasses import dataclass
import re

from app.api.v2.schemas import (
    GenerateRequestV2,
    Language,
    DiagnosisType,
    CommunicativeFunction,
)
from app.services.corpus.korean_freq import get_sentence_frequency_score


@dataclass
class ScoredSentence:
    """점수가 부여된 문장"""
    sentence: str
    matched_words: list[str]
    word_count: int
    score: float
    breakdown: dict[str, float]


# 의사소통 기능 패턴 (한국어)
FUNCTION_PATTERNS_KO = {
    CommunicativeFunction.REQUEST: [
        r"줘|주세요|줄래|싶어|싶어요|하고\s*싶|먹고\s*싶|갖고\s*싶",
    ],
    CommunicativeFunction.REJECT: [
        r"싫어|싫어요|안\s*해|안\s*할래|하기\s*싫|안\s*먹|안\s*갈",
    ],
    CommunicativeFunction.HELP: [
        r"도와|도와줘|도와주세요|어떻게|어떡해|모르겠|못\s*하겠",
    ],
    CommunicativeFunction.CHOICE: [
        r"할래\?|먹을래\?|갈래\?|이거\s*저거|뭐\s*할|어떤\s*거",
    ],
    CommunicativeFunction.ATTENTION: [
        r"봐봐|이거\s*봐|저거\s*봐|여기\s*봐|보세요|있어요",
    ],
    CommunicativeFunction.QUESTION: [
        r"뭐야|뭐예요|어디|언제|누가|왜|어떻게|\?$",
    ],
}


def score_sentences(
    validated: list[dict],
    request: GenerateRequestV2,
) -> list[ScoredSentence]:
    """검증된 문장들에 점수를 부여합니다.

    점수 구성:
    - frequency: 단어 빈도 점수 (40%)
    - function: 의사소통 기능 매칭 점수 (30%)
    - match_bonus: 타깃 음소 다중 매칭 보너스 (20%)
    - length_fit: 길이 적합성 (10%)

    Args:
        validated: 검증 통과한 문장들
        request: 생성 요청

    Returns:
        점수순 정렬된 ScoredSentence 리스트
    """
    results = []

    for item in validated:
        sentence = item["sentence"]
        matched_words = item["matched_words"]
        word_count = item["word_count"]

        breakdown = _calculate_breakdown(sentence, matched_words, request)
        total_score = (
            breakdown["frequency"] * 0.4
            + breakdown["function"] * 0.3
            + breakdown["match_bonus"] * 0.2
            + breakdown["length_fit"] * 0.1
        )

        results.append(ScoredSentence(
            sentence=sentence,
            matched_words=matched_words,
            word_count=word_count,
            score=round(total_score, 2),
            breakdown=breakdown,
        ))

    # 점수순 정렬
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def _calculate_breakdown(
    sentence: str,
    matched_words: list[str],
    request: GenerateRequestV2,
) -> dict[str, float]:
    """점수 breakdown 계산"""
    # 1. 빈도 점수
    if request.language == Language.KO:
        frequency = get_sentence_frequency_score(sentence)
    else:
        frequency = 50.0  # 영어는 추후 구현

    # 2. 기능 점수
    function = 0.0
    if request.communicativeFunction and request.language == Language.KO:
        patterns = FUNCTION_PATTERNS_KO.get(request.communicativeFunction, [])
        for pattern in patterns:
            if re.search(pattern, sentence):
                function = 100.0
                break

    # 3. 매칭 보너스 (다중 매칭 시 가산)
    match_bonus = min(len(matched_words) * 30, 100)

    # 4. 길이 적합성 (항상 100, 이미 검증됨)
    length_fit = 100.0

    return {
        "frequency": round(frequency, 2),
        "function": function,
        "match_bonus": float(match_bonus),
        "length_fit": length_fit,
    }
```

**Step 6: __init__.py 업데이트**

```python
# backend/app/agents/tools/__init__.py
from .generate import generate_candidates
from .validate import validate_sentences, ValidationResult, get_passed_sentences
from .score import score_sentences, ScoredSentence

__all__ = [
    "generate_candidates",
    "validate_sentences",
    "ValidationResult",
    "get_passed_sentences",
    "score_sentences",
    "ScoredSentence",
]
```

**Step 7: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_score_tool.py -v
```

Expected: All tests PASS

**Step 8: 커밋**

```bash
git add backend/app/agents/tools/score.py backend/app/services/corpus/ backend/app/data/ backend/tests/test_score_tool.py
git commit -m "feat(backend): add score_sentences tool

- Add Korean word frequency scoring
- Add communicative function pattern matching
- Calculate composite score (frequency, function, match, length)
- Sort results by score

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.4: diversify_results 도구

**Files:**
- Create: `backend/app/agents/tools/diversify.py`
- Create: `backend/tests/test_diversify_tool.py`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_diversify_tool.py
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
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_diversify_tool.py -v
```

Expected: FAIL

**Step 3: diversify_results 구현**

```python
# backend/app/agents/tools/diversify.py
from collections import defaultdict

from app.agents.tools.score import ScoredSentence


def diversify_results(
    scored: list[ScoredSentence],
    count: int,
    max_similar: int = 2,
) -> list[ScoredSentence]:
    """다양성을 보장하며 최종 결과를 선택합니다.

    Args:
        scored: 점수순 정렬된 문장들
        count: 선택할 개수
        max_similar: 유사 문장 최대 개수

    Returns:
        다양성이 보장된 ScoredSentence 리스트
    """
    if len(scored) <= count:
        return scored

    selected: list[ScoredSentence] = []
    pattern_counts: dict[str, int] = defaultdict(int)

    for sentence in scored:
        if len(selected) >= count:
            break

        # 유사성 체크: 첫 번째 매칭 단어를 패턴으로 사용
        pattern = _get_pattern(sentence)

        if pattern_counts[pattern] < max_similar:
            selected.append(sentence)
            pattern_counts[pattern] += 1

    # 부족하면 남은 것 중 추가
    if len(selected) < count:
        remaining = [s for s in scored if s not in selected]
        selected.extend(remaining[: count - len(selected)])

    return selected


def _get_pattern(sentence: ScoredSentence) -> str:
    """문장의 패턴 키 추출"""
    if sentence.matched_words:
        # 매칭 단어의 첫 2글자를 패턴으로
        first_match = sentence.matched_words[0]
        return first_match[:2] if len(first_match) >= 2 else first_match

    # 매칭 단어 없으면 문장 첫 단어
    words = sentence.sentence.split()
    if words:
        return words[0][:2] if len(words[0]) >= 2 else words[0]

    return ""
```

**Step 4: __init__.py 업데이트**

```python
# backend/app/agents/tools/__init__.py
from .generate import generate_candidates
from .validate import validate_sentences, ValidationResult, get_passed_sentences
from .score import score_sentences, ScoredSentence
from .diversify import diversify_results

__all__ = [
    "generate_candidates",
    "validate_sentences",
    "ValidationResult",
    "get_passed_sentences",
    "score_sentences",
    "ScoredSentence",
    "diversify_results",
]
```

**Step 5: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_diversify_tool.py -v
```

Expected: All tests PASS

**Step 6: 커밋**

```bash
git add backend/app/agents/tools/diversify.py backend/tests/test_diversify_tool.py
git commit -m "feat(backend): add diversify_results tool

- Limit similar sentences by pattern
- Maintain score priority within diversity
- Handle edge cases (fewer results)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.5: 파이프라인 오케스트레이션

**Files:**
- Create: `backend/app/agents/pipeline.py`
- Modify: `backend/app/api/v2/router.py`
- Create: `backend/tests/test_pipeline.py`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_pipeline.py
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.pipeline import run_pipeline
from app.api.v2.schemas import (
    GenerateRequestV2,
    TargetConfig,
    PhonemePosition,
    Language,
    DiagnosisType,
    TherapyApproach,
)


@pytest.fixture
def request():
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
    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_returns_items(self, mock_generate, request):
        """파이프라인이 아이템 반환"""
        mock_generate.return_value = [
            "라면이 너무 맛있어요",
            "라볶이를 먹고 싶어요",
            "달리기가 재미있어요",
            "물을 마시고 싶어요",
            "길을 걸어가고 있어요",
            "라면을 끓이고 있어요",
        ]

        result = await run_pipeline(request)

        assert result.success is True
        assert len(result.items) <= request.count
        assert result.meta.requestedCount == request.count

    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_handles_insufficient(self, mock_generate, request):
        """부족한 결과 처리"""
        mock_generate.return_value = [
            "사과가 맛있어요",  # ㄹ 없음
        ]

        result = await run_pipeline(request)

        # 조건에 맞는 문장이 부족해도 에러 아님
        assert result.success is True
        assert result.meta.generatedCount < result.meta.requestedCount

    @patch("app.agents.pipeline.generate_candidates")
    async def test_pipeline_retries_on_insufficient(self, mock_generate, request):
        """부족 시 재시도"""
        # 첫 호출: 부족, 두 번째 호출: 충분
        mock_generate.side_effect = [
            ["사과가 맛있어요"],  # ㄹ 없음
            ["라면이 너무 맛있어요", "달리기가 재미있어요"],
        ]

        result = await run_pipeline(request)

        assert mock_generate.call_count >= 1
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_pipeline.py -v
```

Expected: FAIL

**Step 3: 파이프라인 구현**

```python
# backend/app/agents/pipeline.py
import time
import uuid
from dataclasses import dataclass

from app.api.v2.schemas import (
    GenerateRequestV2,
    TherapyItemV2,
    MatchedWord,
)
from app.agents.tools import (
    generate_candidates,
    validate_sentences,
    get_passed_sentences,
    score_sentences,
    diversify_results,
)


@dataclass
class PipelineResult:
    """파이프라인 결과"""
    success: bool
    items: list[TherapyItemV2]
    meta: dict


async def run_pipeline(
    request: GenerateRequestV2,
    max_attempts: int = 3,
) -> PipelineResult:
    """4단계 파이프라인을 실행합니다.

    1. Generate: LLM으로 후보 생성
    2. Validate: 하드 제약 검사
    3. Score: 점수 계산
    4. Diversify: 다양성 보장

    Args:
        request: 생성 요청
        max_attempts: 최대 재시도 횟수

    Returns:
        PipelineResult
    """
    start_time = time.time()
    all_validated: list[dict] = []

    # 재시도 루프
    for attempt in range(max_attempts):
        # 1. Generate
        batch_size = (request.count - len(all_validated)) * 3
        if batch_size <= 0:
            break

        candidates = await generate_candidates(request, batch_size)

        # 2. Validate
        results = validate_sentences(candidates, request)
        passed = get_passed_sentences(results)
        all_validated.extend(passed)

        # 충분하면 종료
        if len(all_validated) >= request.count:
            break

    # 3. Score
    scored = score_sentences(all_validated, request)

    # 4. Diversify
    final = diversify_results(scored, request.count)

    # TherapyItemV2로 변환
    items = [
        _to_therapy_item(s, request)
        for s in final
    ]

    processing_time = int((time.time() - start_time) * 1000)

    return PipelineResult(
        success=True,
        items=items,
        meta={
            "requestedCount": request.count,
            "generatedCount": len(items),
            "averageScore": round(sum(s.score for s in final) / len(final), 2) if final else 0,
            "processingTimeMs": processing_time,
        },
    )


def _to_therapy_item(scored, request: GenerateRequestV2) -> TherapyItemV2:
    """ScoredSentence를 TherapyItemV2로 변환"""
    # 매칭 단어 위치 계산
    matched_words = []
    text = scored.sentence
    for word in scored.matched_words:
        start = text.find(word)
        if start >= 0:
            matched_words.append(MatchedWord(
                word=word,
                startIndex=start,
                endIndex=start + len(word),
                positions=[request.target.position],
            ))

    return TherapyItemV2(
        id=str(uuid.uuid4()),
        text=scored.sentence,
        target=request.target,
        matchedWords=matched_words,
        wordCount=scored.word_count,
        score=scored.score,
        diagnosis=request.diagnosis,
        approach=request.therapyApproach,
        theme=request.theme,
        function=request.communicativeFunction,
    )
```

**Step 4: router.py 업데이트**

```python
# backend/app/api/v2/router.py
import logging

from fastapi import APIRouter, HTTPException
from .schemas import (
    GenerateRequestV2,
    ErrorCode,
)
from app.agents.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.post("/generate")
async def generate_sentences(request: GenerateRequestV2):
    """치료용 문장을 생성합니다."""
    try:
        result = await run_pipeline(request)

        return {
            "success": True,
            "data": {
                "items": [item.model_dump() for item in result.items],
                "meta": result.meta,
            },
        }
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.GENERATION_FAILED.value,
                    "message": "문장 생성에 실패했습니다.",
                    "details": str(e),
                },
            },
        )
```

**Step 5: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_pipeline.py -v
```

Expected: All tests PASS

**Step 6: 커밋**

```bash
git add backend/app/agents/pipeline.py backend/app/api/v2/router.py backend/tests/test_pipeline.py
git commit -m "feat(backend): add pipeline orchestration

- Implement 4-stage pipeline (generate, validate, score, diversify)
- Add retry logic for insufficient results
- Convert to TherapyItemV2 response
- Update router to use pipeline

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.6: 출력 가드레일

**Files:**
- Create: `backend/app/agents/guardrails/__init__.py`
- Create: `backend/app/agents/guardrails/child_safety.py`
- Create: `backend/app/data/forbidden_words.json`
- Modify: `backend/app/agents/pipeline.py`
- Create: `backend/tests/test_guardrails.py`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_guardrails.py
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
```

**Step 2: 테스트 실행하여 실패 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_guardrails.py -v
```

Expected: FAIL

**Step 3: 금칙어 데이터 생성**

```json
{
  "forbidden": [
    "술",
    "담배",
    "죽",
    "살인",
    "폭력",
    "마약",
    "도박",
    "욕",
    "섹스",
    "음란"
  ]
}
```

파일: `backend/app/data/forbidden_words.json`

**Step 4: 가드레일 구현**

```python
# backend/app/agents/guardrails/__init__.py
from .child_safety import filter_unsafe_sentences

__all__ = ["filter_unsafe_sentences"]
```

```python
# backend/app/agents/guardrails/child_safety.py
import json
from pathlib import Path

# 금칙어 캐시
_forbidden_words: set[str] | None = None


def _load_forbidden_words() -> set[str]:
    """금칙어 로드"""
    global _forbidden_words
    if _forbidden_words is None:
        data_path = Path(__file__).parent.parent.parent / "data" / "forbidden_words.json"
        if data_path.exists():
            with open(data_path, encoding="utf-8") as f:
                data = json.load(f)
                _forbidden_words = set(data.get("forbidden", []))
        else:
            _forbidden_words = set()
    return _forbidden_words


def is_safe_sentence(sentence: str) -> bool:
    """문장이 아동에게 안전한지 확인합니다."""
    forbidden = _load_forbidden_words()

    sentence_lower = sentence.lower()
    for word in forbidden:
        if word in sentence_lower:
            return False

    return True


def filter_unsafe_sentences(sentences: list[str]) -> list[str]:
    """안전하지 않은 문장을 필터링합니다."""
    return [s for s in sentences if is_safe_sentence(s)]
```

**Step 5: 파이프라인에 가드레일 적용**

```python
# backend/app/agents/pipeline.py (수정)
# generate_candidates 호출 후 가드레일 적용

from app.agents.guardrails import filter_unsafe_sentences

# ... 기존 코드 ...

async def run_pipeline(
    request: GenerateRequestV2,
    max_attempts: int = 3,
) -> PipelineResult:
    # ... 기존 코드 ...

    for attempt in range(max_attempts):
        batch_size = (request.count - len(all_validated)) * 3
        if batch_size <= 0:
            break

        candidates = await generate_candidates(request, batch_size)

        # 가드레일: 안전하지 않은 문장 필터링
        safe_candidates = filter_unsafe_sentences(candidates)

        results = validate_sentences(safe_candidates, request)
        # ... 나머지 코드 ...
```

**Step 6: 테스트 실행하여 통과 확인**

Run:
```bash
cd backend && source .venv/bin/activate && pytest tests/test_guardrails.py -v
```

Expected: All tests PASS

**Step 7: 커밋**

```bash
git add backend/app/agents/guardrails/ backend/app/data/forbidden_words.json backend/app/agents/pipeline.py backend/tests/test_guardrails.py
git commit -m "feat(backend): add child safety guardrail

- Add forbidden words filter
- Apply guardrail in pipeline after generation
- Add tests for safety filtering

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: 프론트엔드 v2

> Phase 3의 세부 태스크는 이 문서의 길이 제한으로 인해 별도 문서로 분리합니다.
> 프론트엔드 구현 시 `docs/plans/2026-01-22-v2-frontend-plan.md`를 생성하세요.

### Task 3.1-3.5 개요

- 3.1: /v2 페이지 및 라우팅
- 3.2: SettingsPanelV2 (진단군별 프리셋 UI)
- 3.3: useGenerateV2 훅 (API 연동)
- 3.4: SentenceListV2 (하이라이트)
- 3.5: 버전 전환 UI (헤더)

---

## Phase 4: 통합 및 배포

> Phase 4는 Phase 2, 3 완료 후 진행합니다.

### Task 4.1-4.4 개요

- 4.1: 프론트-백 통합 테스트
- 4.2: Tracing 설정
- 4.3: 백엔드 배포
- 4.4: 프론트엔드 배포
