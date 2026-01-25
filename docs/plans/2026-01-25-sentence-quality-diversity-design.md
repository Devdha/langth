# 문장 생성 품질 및 다양성 개선 설계

## 문제 정의

### 품질 문제
1. **어색한 표현**: 문법은 맞지만 아이가 실제로 쓰지 않을 것 같은 표현
2. **맥락 없는 문장**: 주어나 상황 설명 없이 뜬금없는 문장
3. **의미 반복**: 같은 의미가 문장 내에서 반복

### 다양성 문제
1. **동일한 문장 구조**: "~가 ~를 ~해요" 패턴만 반복
2. **동일한 어휘**: 같은 단어가 여러 문장에 반복 등장

## 해결 방향: 하이브리드 접근법

프롬프트 개선으로 1차 품질 확보 + 후처리로 다양성 보장

## 상세 설계

### 1단계: 프롬프트 개선 (품질 향상)

#### 안티패턴 명시
기존의 추상적 지시 대신, 피해야 할 패턴을 명시:

```
❌ 피해야 할 패턴:
- "라면이 너무 맛있어요" → 어른 말투, 아이는 "라면 맛있어!"라고 함
- "맛있는 라면을 맛있게 먹어요" → 의미 반복 (맛있는/맛있게)
- "라면을 먹어요" → 맥락 없음, 누가? 왜?
- "~가 ~를 ~해요" 구조만 반복 → 다양한 문장 구조 필요

✅ 좋은 예시:
- "엄마, 라면 먹고 싶어!" (요청, 호칭 포함)
- "라면 냄새 좋다~" (감탄)
- "이 라면 뜨거워?" (질문)
- "라면 다 먹었어!" (완료 보고)
```

#### 구조 다양성 요구
- 서술문, 요청문, 질문문, 감탄문 골고루 생성하도록 명시
- 호칭(엄마, 아빠 등) 포함 문장 권장

### 2단계: 후처리 필터링 (다양성 확보)

#### Hard Filter (탈락)
```python
def check_semantic_repetition(sentence: str) -> bool:
    """의미 반복 검출 - 동일 어근이 2회 이상 등장"""
    # 예: "맛있는 라면을 맛있게" → True (탈락)
    pass

def check_minimal_context(sentence: str) -> bool:
    """최소 맥락 검사 - 주어 없이 목적어+서술어만 있는지"""
    # 예: "라면을 먹어요" → True (탈락)
    pass
```

#### Soft Scoring (점수 조정)
```python
def calculate_diversity_penalty(
    sentence: str,
    already_selected: list[str]
) -> float:
    """다양성 페널티 계산"""
    penalty = 0.0

    # 1. 구조 유사도 체크
    structure = extract_sentence_structure(sentence)
    for s in already_selected:
        if is_similar_structure(structure, extract_sentence_structure(s)):
            penalty += 15.0

    # 2. 어휘 중복 체크
    nouns = extract_nouns(sentence)
    for s in already_selected:
        overlap_count = count_noun_overlap(nouns, extract_nouns(s))
        penalty += overlap_count * 10.0

    return penalty
```

### 3단계: 측정 지표

#### 파이프라인 로그 강화
```python
@dataclass
class PipelineMetrics:
    generated_count: int
    validation_passed: int
    validation_rate: float
    unique_structures: int
    vocabulary_diversity: float  # unique_nouns / total_nouns
    semantic_duplicates_filtered: int
    final_candidates: int
```

#### 로그 출력 예시
```
[Pipeline 리포트]
- 생성: 30개
- Validation 통과: 24개 (80%)
- 구조 유형: 5종류
- 어휘 다양성: 45/72 (62%)
- 의미 반복 탈락: 2개
- 최종 후보: 22개
```

## 구현 계획

| 순서 | 작업 | 파일 | 예상 효과 |
|------|------|------|----------|
| 1 | 프롬프트에 안티패턴 추가 | `builder.py` | 품질 즉시 개선 |
| 2 | 의미 반복 hard filter | `validate.py` | 명백히 나쁜 문장 제거 |
| 3 | 다양성 soft scoring | `score.py` | 상위 문장 다양화 |
| 4 | 로그/지표 추가 | `pipeline.py` | 효과 측정 가능 |

## 기대 효과

- 품질: 안티패턴 명시로 어색한 문장 감소
- 다양성: 점수 조정으로 다양한 문장이 상위 노출
- 측정: 지표를 통해 개선 효과 정량화 가능
