# v2 치료 자극 선정 엔진 설계 문서

> 작성일: 2026-01-22

## 1. 개요

### 프로젝트 목표
현재 "문장 생성기"를 임상적으로 유효한 **"치료 자극 선정 엔진(Stimulus Selection Engine)"**으로 업그레이드

### 라우팅 구조
```
/          → v1 (기존 유지)
/v2        → v2 (신규)
```

### 버전 전환 UI
- 헤더 오른쪽에 버전 전환 링크
- v1 헤더: "v2 체험하기 →" 링크
- v2 헤더: "← v1으로 돌아가기" 링크

### 주요 변경 범위

| 영역 | v1 | v2 |
|------|----|----|
| 음소 필터 | 초성/종성 둘 다 | 위치(초성/중성/종성) 선택 가능 |
| 영어 필터 | 철자 기반 | CMUdict 발음 기반 |
| 테마/기능 | 테마만 | 진단군별 프리셋 (SSD: 테마, ASD: 기능) |
| 치료 접근 | 없음 | Minimal Pairs / Complexity 등 선택 |
| 난이도 | 어절 수만 | 어절 수 + 빈도/친숙도 점수 |
| 하이라이트 | 없음 | 타깃 음소 포함 단어 강조 |

---

## 2. 아키텍처

```
[Cloudflare Workers]          [Python Backend]
     Next.js                    FastAPI + OpenAI Agents SDK
        │                            │
   ┌────┴────┐                 ┌─────┴─────┐
   │ /       │ (v1 프론트)     │           │
   │ /v2     │ (v2 프론트)     │  /api/v2  │
   │         │                 │ /generate │
   └────┬────┘                 └─────┬─────┘
        │                            │
        │     POST /api/v2/generate  │
        │ ─────────────────────────► │
        │                            │
        │     { items: [...] }       │
        │ ◄───────────────────────── │
        │                            │
                               ┌─────┴─────┐
                               │ Memory    │
                               │ - CMUdict │
                               │ - 빈도코퍼스│
                               │ - OpenAI  │
                               └───────────┘
```

---

## 3. 타입 정의

### 진단군 및 치료 접근법

```typescript
// 지원 진단군
type DiagnosisType = 'SSD' | 'ASD' | 'LD';
// SSD: Speech Sound Disorder (말소리장애)
// ASD: Autism Spectrum Disorder (자폐스펙트럼)
// LD: Language Delay (언어발달지연)

// 치료 접근법
type TherapyApproach =
  | 'minimal_pairs'      // 최소대립쌍
  | 'maximal_oppositions' // 최대대립
  | 'complexity'         // 복잡도 접근
  | 'core_vocabulary';   // 핵심어휘

// 의사소통 기능 (ASD용)
type CommunicativeFunction =
  | 'request'    // 요청
  | 'reject'     // 거절
  | 'help'       // 도움요청
  | 'choice'     // 선택
  | 'attention'  // 주목끌기
  | 'question';  // 질문

// 음소 위치
type PhonemePosition = 'onset' | 'nucleus' | 'coda' | 'any';
```

### v2 설정 모델

```typescript
interface GameSettingsV2 {
  // 기본
  language: 'ko' | 'en';
  age: 3 | 4 | 5 | 6 | 7;
  count: number;

  // 타깃 음소
  target: {
    phoneme: string;
    position: PhonemePosition;
    minOccurrences: number;
  };

  // 문장 구조
  sentenceLength: number;
  lengthUnit: 'eojeol' | 'word';

  // 진단군별 설정
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  theme?: string;
  communicativeFunction?: CommunicativeFunction;
}
```

### 결과 데이터

```typescript
interface TherapyItemV2 {
  id: string;
  text: string;
  target: {
    phoneme: string;
    position: PhonemePosition;
  };
  matchedWords: MatchedWord[];
  wordCount: number;
  score: number;
  diagnosis: DiagnosisType;
  approach: TherapyApproach;
  theme?: string;
  function?: CommunicativeFunction;
}

interface MatchedWord {
  word: string;
  startIndex: number;
  endIndex: number;
  positions: PhonemePosition[];
}
```

---

## 4. 파이프라인 아키텍처

### 4단계 파이프라인

```
[1. Generate] → [2. Validate] → [3. Score] → [4. Diversify] → 최종 결과
```

### OpenAI Agents SDK 기반 구현

```python
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

@function_tool
async def generate_candidates(request: GenerateRequest) -> list[str]:
    """LLM으로 후보 문장을 대량 생성합니다."""
    ...

@function_tool
async def validate_sentences(sentences: list[str], request: GenerateRequest) -> list[dict]:
    """하드 제약(길이, 음소, 위치)을 검사합니다."""
    ...

@function_tool
async def score_sentences(validated: list[dict], request: GenerateRequest) -> list[ScoredSentence]:
    """빈도/기능성/문맥 점수를 계산합니다."""
    ...

@function_tool
async def diversify_results(scored: list[ScoredSentence], count: int) -> list[ScoredSentence]:
    """다양성을 보장하며 최종 N개를 선택합니다."""
    ...
```

### 코드 기반 오케스트레이션 (권장)

```python
async def run_pipeline_deterministic(request: GenerateRequest) -> list[ScoredSentence]:
    # 1. Generate
    candidates = await generate_candidates(request)

    # 2. Validate
    validated = await validate_sentences(candidates, request)

    # 3. Score
    scored = await score_sentences(validated, request)

    # 4. Diversify
    final = await diversify_results(scored, request.count)

    return final
```

---

## 5. 음소 탐지 로직

### 한국어 (hgtk 기반)

```python
import hgtk

def has_phoneme_at_position(word: str, phoneme: str, position: str) -> bool:
    for char in word:
        try:
            cho, jung, jong = hgtk.letter.decompose(char)
        except:
            continue

        if position == 'onset' and cho == phoneme:
            # 'ㅇ' 초성은 제외 (무음)
            if phoneme == 'ㅇ':
                continue
            return True
        if position == 'nucleus' and jung == phoneme:
            return True
        if position == 'coda' and jong == phoneme:
            return True
        if position == 'any' and phoneme in (cho, jung, jong):
            if phoneme == 'ㅇ' and cho == 'ㅇ':
                continue  # 초성 ㅇ 제외
            return True

    return False
```

### 영어 (CMUdict 기반)

```python
import pronouncing
import g2p_en

g2p = g2p_en.G2p()

def get_phonemes(word: str) -> list[str]:
    phones = pronouncing.phones_for_word(word.lower())
    if phones:
        return [p.rstrip('012') for p in phones[0].split()]
    # OOV: 뉴럴넷 기반 예측
    return [p.rstrip('012') for p in g2p(word) if p.isalpha()]

def has_target_phoneme_en(sentence: str, target: str, min_occurrences: int = 1) -> tuple[bool, list[str]]:
    words = sentence.split()
    matched_words = []

    for word in words:
        clean = ''.join(c for c in word if c.isalpha())
        phonemes = get_phonemes(clean)
        if phonemes and target in phonemes:
            matched_words.append(word)

    return (len(matched_words) >= min_occurrences, matched_words)
```

---

## 6. 진단군별 프리셋

```typescript
const DIAGNOSIS_PRESETS = {
  SSD: {
    availableApproaches: ['minimal_pairs', 'maximal_oppositions', 'complexity', 'core_vocabulary'],
    defaultApproach: 'minimal_pairs',
    useTheme: true,
    useFunction: false,
  },
  ASD: {
    availableApproaches: ['core_vocabulary'],
    defaultApproach: 'core_vocabulary',
    useTheme: false,
    useFunction: true,
  },
  LD: {
    availableApproaches: ['minimal_pairs', 'core_vocabulary'],
    defaultApproach: 'core_vocabulary',
    useTheme: true,
    useFunction: true,
  },
};
```

---

## 7. API 스펙

### Request

```typescript
interface GenerateRequestV2 {
  language: 'ko' | 'en';
  age: 3 | 4 | 5 | 6 | 7;
  count: number;
  target: {
    phoneme: string;
    position: 'onset' | 'nucleus' | 'coda' | 'any';
    minOccurrences: number;
  };
  sentenceLength: number;
  diagnosis: 'SSD' | 'ASD' | 'LD';
  therapyApproach: string;
  theme?: string;
  communicativeFunction?: string;
}
```

### Response (성공)

```typescript
interface GenerateResponseV2 {
  success: true;
  data: {
    items: TherapyItemV2[];
    meta: {
      requestedCount: number;
      generatedCount: number;
      averageScore: number;
      processingTimeMs: number;
    };
  };
}
```

### Response (실패)

```typescript
interface ErrorResponseV2 {
  success: false;
  error: {
    code: 'INVALID_REQUEST' | 'GENERATION_FAILED' | 'INSUFFICIENT_RESULTS' | 'RATE_LIMITED' | 'SERVICE_UNAVAILABLE';
    message: string;
    details?: string;
  };
}
```

---

## 8. Guardrails & Tracing

### 출력 가드레일 (아동 안전)

```python
from agents import output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def child_content_filter(ctx, agent, output):
    """아동 부적절 콘텐츠 필터링"""
    # 금칙어 체크 및 필터링
    ...
```

### Tracing 설정

| 환경 | 설정 |
|------|------|
| 개발/테스트 | 활성화 (기본값) |
| 프로덕션 | 민감 데이터 제외 |

```python
from agents import RunConfig

config = RunConfig(
    trace_include_sensitive_data=False,  # 프로덕션
)
```

---

## 9. 파일 구조

### 프론트엔드

```
app/
├── v2/
│   └── page.tsx
components/
├── v2/
│   ├── SettingsPanelV2.tsx
│   ├── DiagnosisSelector.tsx
│   ├── PhonemeSelector.tsx
│   ├── SentenceListV2.tsx
│   └── HighlightedText.tsx
hooks/
├── useGenerateV2.ts
lib/
├── v2/
│   ├── api.ts
│   └── constants.ts
types/
├── v2.ts
```

### 백엔드

```
backend/
├── app/
│   ├── main.py
│   ├── api/v2/
│   │   ├── router.py
│   │   └── schemas.py
│   ├── agents/
│   │   ├── pipeline.py
│   │   ├── tools/
│   │   │   ├── generate.py
│   │   │   ├── validate.py
│   │   │   ├── score.py
│   │   │   └── diversify.py
│   │   └── guardrails/
│   │       └── child_safety.py
│   └── services/
│       ├── phoneme/
│       │   ├── korean.py
│       │   └── english.py
│       └── corpus/
│           ├── korean_freq.py
│           └── english_freq.py
├── tests/
└── Dockerfile
```

---

## 10. 구현 순서

### Phase 1: 기반 구축 (백엔드)
- 1.1 프로젝트 셋업 (FastAPI + openai-agents)
- 1.2 한국어 음소 탐지
- 1.3 영어 음소 탐지
- 1.4 기본 API 엔드포인트

### Phase 2: 파이프라인 구현 (백엔드)
- 2.1 generate_candidates 도구
- 2.2 validate_sentences 도구
- 2.3 score_sentences 도구
- 2.4 diversify_results 도구
- 2.5 파이프라인 오케스트레이션
- 2.6 출력 가드레일

### Phase 3: 프론트엔드 v2
- 3.1 /v2 페이지 및 라우팅
- 3.2 SettingsPanelV2
- 3.3 useGenerateV2 훅
- 3.4 SentenceListV2 (하이라이트)
- 3.5 버전 전환 UI

### Phase 4: 통합 및 배포
- 4.1 프론트-백 통합 테스트
- 4.2 Tracing 설정
- 4.3 백엔드 배포
- 4.4 프론트엔드 배포

---

## 11. 의존성

### 백엔드 (Python)

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "openai-agents>=0.6.9",
    "pydantic>=2.0.0",
    "pronouncing>=0.2.0",
    "g2p-en>=2.1.0",
    "hgtk>=0.2.0",
    "python-dotenv>=1.0.0",
]
```

### 프론트엔드 (기존 유지)

- next@15.1.11
- react@19.2.3
- framer-motion@12.25.0
- lucide-react@0.562.0
- tailwindcss@4
