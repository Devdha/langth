"""Prompt builder for therapy sentence generation.

This module builds prompts for LLM-based therapy sentence generation,
supporting both Korean and English languages with diagnosis-specific
customization.

Example:
    >>> from app.api.v2.schemas import GenerateRequestV2, Language, ...
    >>> request = GenerateRequestV2(language=Language.KO, age=5, ...)
    >>> prompt = build_generation_prompt(request, batch_size=30)
"""

from app.api.v2.schemas import (
    GenerateRequestV2,
    Language,
    PhonemePosition,
    CommunicativeFunction,
)

# Theme descriptions for sentence context
THEME_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "daily": {
        "ko": "일상생활 (먹기, 자기, 놀기, 옷 입기 등)",
        "en": "daily life (eating, sleeping, playing, dressing, etc.)",
    },
    "animals": {
        "ko": "동물 (강아지, 고양이, 토끼, 새 등)",
        "en": "animals (dogs, cats, rabbits, birds, etc.)",
    },
    "food": {
        "ko": "음식 (과일, 채소, 간식, 음료 등)",
        "en": "food (fruits, vegetables, snacks, drinks, etc.)",
    },
    "family": {
        "ko": "가족 (엄마, 아빠, 형제, 조부모 등)",
        "en": "family (mom, dad, siblings, grandparents, etc.)",
    },
    "school": {
        "ko": "학교/유치원 (선생님, 친구, 공부, 놀이 등)",
        "en": "school (teacher, friends, studying, playing, etc.)",
    },
    "nature": {
        "ko": "자연 (날씨, 계절, 꽃, 나무 등)",
        "en": "nature (weather, seasons, flowers, trees, etc.)",
    },
    "transportation": {
        "ko": "교통수단 (자동차, 버스, 비행기, 자전거 등)",
        "en": "transportation (cars, buses, airplanes, bicycles, etc.)",
    },
    "toys": {
        "ko": "장난감 (인형, 블록, 공, 그림 등)",
        "en": "toys (dolls, blocks, balls, drawings, etc.)",
    },
}

# Communicative function descriptions
FUNCTION_DESCRIPTIONS: dict[CommunicativeFunction, dict[str, str]] = {
    CommunicativeFunction.REQUEST: {
        "ko": "요청하기 (물건, 도움, 행동을 요청하는 문장)",
        "en": "requesting (sentences asking for objects, help, or actions)",
    },
    CommunicativeFunction.REJECT: {
        "ko": "거부하기 (싫어요, 아니요 등 거부 표현)",
        "en": "rejecting (expressing 'no', 'I don't want', refusal)",
    },
    CommunicativeFunction.HELP: {
        "ko": "도움 요청하기 (도와주세요, 열어주세요 등)",
        "en": "asking for help (please help, open it for me, etc.)",
    },
    CommunicativeFunction.CHOICE: {
        "ko": "선택하기 (이것 또는 저것 선택 표현)",
        "en": "making choices (choosing between options)",
    },
    CommunicativeFunction.ATTENTION: {
        "ko": "주의 끌기 (봐주세요, 여기요 등)",
        "en": "getting attention (look at me, over here, etc.)",
    },
    CommunicativeFunction.QUESTION: {
        "ko": "질문하기 (뭐야?, 어디야?, 왜? 등)",
        "en": "asking questions (what, where, why, etc.)",
    },
}

# Age-appropriate guidelines
AGE_GUIDELINES: dict[int, dict[str, str]] = {
    3: {
        "ko": "3세: 매우 간단한 문장, 1-2개 핵심 단어, 의성어/의태어 활용",
        "en": "3 years: very simple sentences, 1-2 key words, use onomatopoeia",
    },
    4: {
        "ko": "4세: 간단한 문장, 기본 문법, 친숙한 단어 위주",
        "en": "4 years: simple sentences, basic grammar, familiar vocabulary",
    },
    5: {
        "ko": "5세: 기본 문장, 조사 사용, 간단한 접속 표현",
        "en": "5 years: basic sentences, proper particles, simple conjunctions",
    },
    6: {
        "ko": "6세: 복합 문장 가능, 다양한 조사, 시제 표현",
        "en": "6 years: compound sentences possible, varied particles, tense expressions",
    },
    7: {
        "ko": "7세: 복잡한 문장 구조, 추상적 개념, 비유 표현",
        "en": "7 years: complex sentence structures, abstract concepts, figurative language",
    },
}

# Phoneme position descriptions
POSITION_DESCRIPTIONS: dict[PhonemePosition, dict[str, str]] = {
    PhonemePosition.ONSET: {
        "ko": "초성 (음절의 첫소리)",
        "en": "onset (beginning of syllable)",
    },
    PhonemePosition.NUCLEUS: {
        "ko": "중성 (모음)",
        "en": "nucleus (vowel)",
    },
    PhonemePosition.CODA: {
        "ko": "종성 (음절의 끝소리/받침)",
        "en": "coda (end of syllable)",
    },
    PhonemePosition.ANY: {
        "ko": "모든 위치 (초성, 중성, 종성 모두 가능)",
        "en": "any position (onset, nucleus, or coda)",
    },
}


def build_generation_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build a prompt for therapy sentence generation.

    Constructs a language-specific prompt based on the generation request
    parameters, including diagnosis type, therapy approach, and optional
    communicative function.

    Args:
        request: The generation request containing all parameters.
        batch_size: Number of sentences to generate.

    Returns:
        A formatted prompt string for the LLM.

    Example:
        >>> request = GenerateRequestV2(
        ...     language=Language.KO,
        ...     age=5,
        ...     count=10,
        ...     target=TargetConfig(phoneme="ㄹ", position=PhonemePosition.ONSET),
        ...     sentenceLength=4,
        ...     diagnosis=DiagnosisType.SSD,
        ...     therapyApproach=TherapyApproach.MINIMAL_PAIRS,
        ... )
        >>> prompt = build_generation_prompt(request, batch_size=30)
        >>> "한국어" in prompt
        True
    """
    if request.language == Language.KO:
        return _build_korean_prompt(request, batch_size)
    else:
        return _build_english_prompt(request, batch_size)


def _build_korean_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build a Korean prompt for therapy sentence generation.

    Args:
        request: The generation request.
        batch_size: Number of sentences to generate.

    Returns:
        A Korean prompt string.
    """
    # Get descriptions
    age_guideline = AGE_GUIDELINES.get(request.age, AGE_GUIDELINES[5])["ko"]
    position_desc = POSITION_DESCRIPTIONS[request.target.position]["ko"]

    # Build theme section
    theme_section = ""
    if request.theme:
        theme_desc = THEME_DESCRIPTIONS.get(request.theme, {}).get("ko", request.theme)
        theme_section = f"\n- 주제: {theme_desc}"

    # Build function section for ASD
    function_section = ""
    if request.communicativeFunction:
        func_desc = FUNCTION_DESCRIPTIONS[request.communicativeFunction]["ko"]
        function_section = f"\n- 의사소통 기능: {func_desc}"

    prompt = f"""당신은 아동 언어치료사를 돕는 전문 문장 생성 AI입니다.
다음 조건에 맞는 한국어 치료 문장 {batch_size}개를 생성해주세요.

## 생성 조건

### 기본 정보
- 언어: 한국어
- 대상 아동 연령: {request.age}세
- {age_guideline}

### 문장 구조
- 문장 길이: {request.sentenceLength}어절 (띄어쓰기 기준)
- 목표 음소: '{request.target.phoneme}'
- 음소 위치: {position_desc}
- 최소 출현 횟수: {request.target.minOccurrences}회 이상

### 치료 정보
- 진단명: {request.diagnosis.value}
- 치료 접근법: {request.therapyApproach.value}{theme_section}{function_section}

## 중요 지침

1. **아동 적절성**: 모든 문장은 아동에게 안전하고 적절한 내용이어야 합니다.
   - 폭력, 공포, 부정적 감정 표현 금지
   - 긍정적이고 밝은 내용 위주

2. **음소 정확성**: 목표 음소 '{request.target.phoneme}'이(가) 지정된 위치({position_desc})에 {request.target.minOccurrences}회 이상 포함되어야 합니다.

3. **자연스러움**: 문장이 자연스럽고 일상에서 사용할 수 있는 표현이어야 합니다.

4. **다양성**: 생성되는 문장들이 서로 다르고 다양해야 합니다.

## 출력 형식

반드시 다음 JSON 형식으로 출력하세요:
```json
{{"sentences": ["문장1", "문장2", "문장3", ...]}}
```

{batch_size}개의 문장을 생성해주세요."""

    return prompt


def _build_english_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build an English prompt for therapy sentence generation.

    Args:
        request: The generation request.
        batch_size: Number of sentences to generate.

    Returns:
        An English prompt string.
    """
    # Get descriptions
    age_guideline = AGE_GUIDELINES.get(request.age, AGE_GUIDELINES[5])["en"]
    position_desc = POSITION_DESCRIPTIONS[request.target.position]["en"]

    # Build theme section
    theme_section = ""
    if request.theme:
        theme_desc = THEME_DESCRIPTIONS.get(request.theme, {}).get("en", request.theme)
        theme_section = f"\n- Theme: {theme_desc}"

    # Build function section for ASD
    function_section = ""
    if request.communicativeFunction:
        func_desc = FUNCTION_DESCRIPTIONS[request.communicativeFunction]["en"]
        function_section = f"\n- Communicative function: {func_desc}"

    prompt = f"""You are a specialized AI assistant helping speech-language pathologists generate therapy sentences.
Please generate {batch_size} English therapy sentences according to the following requirements.

## Generation Requirements

### Basic Information
- Language: English
- Target child age: {request.age} years old
- {age_guideline}

### Sentence Structure
- Sentence length: {request.sentenceLength} words
- Target phoneme: '{request.target.phoneme}'
- Phoneme position: {position_desc}
- Minimum occurrences: {request.target.minOccurrences} or more

### Therapy Information
- Diagnosis: {request.diagnosis.value}
- Therapy approach: {request.therapyApproach.value}{theme_section}{function_section}

## Important Guidelines

1. **Child appropriateness**: All sentences must be safe and appropriate for children.
   - No violence, fear, or negative emotional content
   - Focus on positive and cheerful content

2. **Phoneme accuracy**: The target phoneme '{request.target.phoneme}' must appear in the specified position ({position_desc}) at least {request.target.minOccurrences} time(s).

3. **Naturalness**: Sentences should be natural and usable in everyday situations.

4. **Diversity**: Generated sentences should be varied and different from each other.

## Output Format

Output MUST be in the following JSON format:
```json
{{"sentences": ["sentence1", "sentence2", "sentence3", ...]}}
```

Please generate {batch_size} sentences."""

    return prompt
