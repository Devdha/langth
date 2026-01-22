"""Prompt builder for therapy sentence generation.

This module builds prompts for LLM-based therapy sentence generation,
supporting both Korean and English languages with diagnosis-specific
customization and therapy approach-specific prompt builders.

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
    TherapyApproach,
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

    Routes to different prompt builders based on therapy approach:
    - minimal_pairs/maximal_oppositions -> _build_contrast_prompt
    - complexity -> _build_complexity_prompt
    - core_vocabulary -> _build_core_vocab_prompt

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
    lang = "ko" if request.language == Language.KO else "en"

    # Route based on therapy approach
    if request.therapyApproach in (
        TherapyApproach.MINIMAL_PAIRS,
        TherapyApproach.MAXIMAL_OPPOSITIONS,
    ):
        return _build_contrast_prompt(request, batch_size, lang)
    elif request.therapyApproach == TherapyApproach.COMPLEXITY:
        return _build_complexity_prompt(request, batch_size, lang)
    elif request.therapyApproach == TherapyApproach.CORE_VOCABULARY:
        return _build_core_vocab_prompt(request, batch_size, lang)
    else:
        # Fallback to default token-based prompt
        if lang == "ko":
            return _build_korean_prompt(request, batch_size)
        else:
            return _build_english_prompt(request, batch_size)


def _get_common_context(request: GenerateRequestV2, lang: str) -> dict[str, str]:
    """Get common context values for prompt building.

    Args:
        request: The generation request.
        lang: Language code ("ko" or "en").

    Returns:
        Dictionary with common context values.
    """
    age_guideline = AGE_GUIDELINES.get(request.age, AGE_GUIDELINES[5])[lang]
    position_desc = POSITION_DESCRIPTIONS[request.target.position][lang]

    theme_section = ""
    if request.theme:
        theme_desc = THEME_DESCRIPTIONS.get(request.theme, {}).get(lang, request.theme)
        theme_section = (
            f"\n- 주제: {theme_desc}" if lang == "ko" else f"\n- Theme: {theme_desc}"
        )

    function_section = ""
    if request.communicativeFunction:
        func_desc = FUNCTION_DESCRIPTIONS[request.communicativeFunction][lang]
        function_section = (
            f"\n- 의사소통 기능: {func_desc}"
            if lang == "ko"
            else f"\n- Communicative function: {func_desc}"
        )

    return {
        "age_guideline": age_guideline,
        "position_desc": position_desc,
        "theme_section": theme_section,
        "function_section": function_section,
    }


def _generate_token_examples(token_count: int, lang: str) -> str:
    """Generate examples showing correct token count.

    Args:
        token_count: The required number of tokens.
        lang: Language code ("ko" or "en").

    Returns:
        A string with examples of correct token counts.
    """
    ko_examples = {
        2: [
            (["사과", "먹어요"], "request"),
            (["강아지", "귀여워"], "attention"),
        ],
        3: [
            (["고양이가", "밥을", "먹어요"], "request"),
            (["엄마가", "책을", "읽어요"], "attention"),
        ],
        4: [
            (["문", "좀", "닫아", "줘"], "request"),
            (["아빠가", "요리를", "하고", "있어요"], "attention"),
        ],
        5: [
            (["엄마가", "맛있는", "간식을", "만들어", "주었어요"], "request"),
            (["우리", "가족이", "함께", "공원에", "갔어요"], "attention"),
        ],
    }

    en_examples = {
        2: [
            (["Please", "help"], "request"),
            (["Look", "here"], "attention"),
        ],
        3: [
            (["I", "want", "milk"], "request"),
            (["Cat", "is", "sleeping"], "attention"),
        ],
        4: [
            (["Can", "I", "have", "cookies"], "request"),
            (["The", "dog", "is", "running"], "attention"),
        ],
        5: [
            (["Please", "help", "me", "open", "this"], "help"),
            (["The", "rabbit", "is", "eating", "carrots"], "attention"),
        ],
    }

    examples = ko_examples if lang == "ko" else en_examples

    if token_count not in examples:
        return ""

    if lang == "ko":
        lines = [f"**{token_count}개 토큰 예시:**"]
        for tokens, func in examples[token_count]:
            tokens_json = str(tokens).replace("'", '"')
            lines.append(f'  - {{"tokens": {tokens_json}, "function": "{func}"}}')
    else:
        lines = [f"**{token_count}-token examples:**"]
        for tokens, func in examples[token_count]:
            tokens_json = str(tokens).replace("'", '"')
            lines.append(f'  - {{"tokens": {tokens_json}, "function": "{func}"}}')

    return "\n".join(lines)


def _build_contrast_prompt(
    request: GenerateRequestV2, batch_size: int, lang: str
) -> str:
    """Build a prompt for minimal pairs / maximal oppositions therapy.

    This approach generates pairs of words/sentences that differ by one phoneme,
    helping children distinguish between similar sounds.

    Args:
        request: The generation request.
        batch_size: Number of contrast pairs to generate.
        lang: Language code ("ko" or "en").

    Returns:
        A prompt string for contrast-based therapy.
    """
    ctx = _get_common_context(request, lang)
    approach_name = (
        "최소대립쌍" if request.therapyApproach == TherapyApproach.MINIMAL_PAIRS else "최대대립"
    )
    approach_name_en = (
        "minimal pairs"
        if request.therapyApproach == TherapyApproach.MINIMAL_PAIRS
        else "maximal oppositions"
    )

    if lang == "ko":
        return f"""당신은 아동 언어치료사를 돕는 전문 문장 생성 AI입니다.
{approach_name} 치료를 위한 대조 세트 {batch_size}개를 생성해주세요.

## 생성 조건

### 기본 정보
- 언어: 한국어
- 대상 아동 연령: {request.age}세
- {ctx['age_guideline']}

### 문장 구조 (매우 중요!)
- **tokens 배열의 길이가 정확히 {request.sentenceLength}개여야 합니다**
- 서버가 tokens를 join하여 문장을 만듭니다
- 목표 음소: '{request.target.phoneme}'
- 음소 위치: {ctx['position_desc']}

### 치료 정보
- 진단명: {request.diagnosis.value}
- 치료 접근법: {approach_name}{ctx['theme_section']}{ctx['function_section']}

## {approach_name} 설명
- 목표 음소와 대조 음소가 포함된 단어 쌍을 생성합니다
- 예: '라면' vs '나면', '달' vs '탈'
- 각 세트에는 목표 단어와 대조 단어, 그리고 각각을 포함한 문장이 필요합니다

## 중요 지침

1. **토큰 수 정확성**: 모든 문장의 tokens 배열은 정확히 {request.sentenceLength}개 요소를 가져야 합니다
2. **아동 적절성**: 긍정적이고 안전한 내용만 생성
3. **자연스러움**: 일상에서 사용 가능한 표현

## 출력 형식

반드시 다음 JSON 형식으로만 출력하세요:
```json
{{"sets": [
  {{
    "target_word": "라면",
    "contrast_word": "나면",
    "target_sentence": {{"tokens": ["맛있는", "라면을", "먹어요"]}},
    "contrast_sentence": {{"tokens": ["봄이", "나면", "좋아요"]}}
  }}
]}}
```

{batch_size}개의 대조 세트를 생성해주세요. JSON 출력만 허용됩니다."""

    else:
        return f"""You are a specialized AI assistant helping speech-language pathologists.
Please generate {batch_size} contrast sets for {approach_name_en} therapy.

## Generation Requirements

### Basic Information
- Language: English
- Target child age: {request.age} years old
- {ctx['age_guideline']}

### Sentence Structure (CRITICAL!)
- **The tokens array must have exactly {request.sentenceLength} elements**
- The server joins tokens to create the sentence
- Target phoneme: '{request.target.phoneme}'
- Phoneme position: {ctx['position_desc']}

### Therapy Information
- Diagnosis: {request.diagnosis.value}
- Therapy approach: {approach_name_en}{ctx['theme_section']}{ctx['function_section']}

## {approach_name_en.title()} Explanation
- Generate word pairs containing the target phoneme and a contrasting phoneme
- Example: 'rat' vs 'bat', 'sun' vs 'fun'
- Each set needs target word, contrast word, and sentences containing each

## Important Guidelines

1. **Token count accuracy**: All sentence tokens arrays must have exactly {request.sentenceLength} elements
2. **Child appropriateness**: Only positive and safe content
3. **Naturalness**: Use everyday expressions

## Output Format

Output MUST be in the following JSON format only:
```json
{{"sets": [
  {{
    "target_word": "rat",
    "contrast_word": "bat",
    "target_sentence": {{"tokens": ["The", "rat", "ran", "fast"]}},
    "contrast_sentence": {{"tokens": ["The", "bat", "flew", "away"]}}
  }}
]}}
```

Generate {batch_size} contrast sets. JSON output only."""


def _build_complexity_prompt(
    request: GenerateRequestV2, batch_size: int, lang: str
) -> str:
    """Build a prompt for complexity-based therapy.

    This approach generates sentences with varying difficulty levels,
    targeting more complex phoneme combinations.

    Args:
        request: The generation request.
        batch_size: Number of items to generate.
        lang: Language code ("ko" or "en").

    Returns:
        A prompt string for complexity-based therapy.
    """
    ctx = _get_common_context(request, lang)

    if lang == "ko":
        return f"""당신은 아동 언어치료사를 돕는 전문 문장 생성 AI입니다.
복잡성 기반 치료를 위한 문장 {batch_size}개를 난이도별로 생성해주세요.

## 생성 조건

### 기본 정보
- 언어: 한국어
- 대상 아동 연령: {request.age}세
- {ctx['age_guideline']}

### 문장 구조 (매우 중요!)
- **tokens 배열의 길이가 정확히 {request.sentenceLength}개여야 합니다**
- 서버가 tokens를 join하여 문장을 만듭니다
- 목표 음소: '{request.target.phoneme}'
- 음소 위치: {ctx['position_desc']}
- 최소 출현 횟수: {request.target.minOccurrences}회 이상

### 치료 정보
- 진단명: {request.diagnosis.value}
- 치료 접근법: 복잡성 접근법{ctx['theme_section']}{ctx['function_section']}

## 복잡성 접근법 설명
- easy: 목표 음소가 단순한 위치에 있고 주변 음소가 쉬운 경우
- medium: 목표 음소가 자음군이나 약간 복잡한 환경에 있는 경우
- hard: 목표 음소가 복잡한 자음군이나 어려운 음운 환경에 있는 경우

## 중요 지침

1. **토큰 수 정확성**: 모든 문장의 tokens 배열은 정확히 {request.sentenceLength}개 요소를 가져야 합니다
2. **난이도 분포**: easy, medium, hard를 균등하게 분배
3. **아동 적절성**: 긍정적이고 안전한 내용만 생성
4. **target_analysis**: 목표 음소가 어떤 음운 환경에서 나타나는지 설명

## 출력 형식

반드시 다음 JSON 형식으로만 출력하세요:
```json
{{"items": [
  {{
    "tokens": ["라면을", "맛있게", "먹어요"],
    "difficulty": "easy",
    "target_analysis": {{
      "phoneme": "ㄹ",
      "position": "onset",
      "environment": "어두 초성, 모음 앞",
      "complexity_reason": "단순한 음운 환경"
    }}
  }}
]}}
```

{batch_size}개 문장을 생성해주세요. JSON 출력만 허용됩니다."""

    else:
        return f"""You are a specialized AI assistant helping speech-language pathologists.
Please generate {batch_size} sentences for complexity-based therapy with varying difficulty levels.

## Generation Requirements

### Basic Information
- Language: English
- Target child age: {request.age} years old
- {ctx['age_guideline']}

### Sentence Structure (CRITICAL!)
- **The tokens array must have exactly {request.sentenceLength} elements**
- The server joins tokens to create the sentence
- Target phoneme: '{request.target.phoneme}'
- Phoneme position: {ctx['position_desc']}
- Minimum occurrences: {request.target.minOccurrences} or more

### Therapy Information
- Diagnosis: {request.diagnosis.value}
- Therapy approach: complexity approach{ctx['theme_section']}{ctx['function_section']}

## Complexity Approach Explanation
- easy: Target phoneme in simple position with easy surrounding phonemes
- medium: Target phoneme in consonant clusters or slightly complex environments
- hard: Target phoneme in complex clusters or difficult phonological environments

## Important Guidelines

1. **Token count accuracy**: All sentence tokens arrays must have exactly {request.sentenceLength} elements
2. **Difficulty distribution**: Distribute easy, medium, hard evenly
3. **Child appropriateness**: Only positive and safe content
4. **target_analysis**: Explain the phonological environment of the target phoneme

## Output Format

Output MUST be in the following JSON format only:
```json
{{"items": [
  {{
    "tokens": ["The", "rabbit", "runs", "fast"],
    "difficulty": "easy",
    "target_analysis": {{
      "phoneme": "r",
      "position": "onset",
      "environment": "word-initial, before vowel",
      "complexity_reason": "simple phonological environment"
    }}
  }}
]}}
```

Generate {batch_size} sentences. JSON output only."""


def _build_core_vocab_prompt(
    request: GenerateRequestV2, batch_size: int, lang: str
) -> str:
    """Build a prompt for core vocabulary therapy.

    This approach focuses on high-frequency core words that children
    can use across multiple contexts.

    Args:
        request: The generation request.
        batch_size: Number of items to generate.
        lang: Language code ("ko" or "en").

    Returns:
        A prompt string for core vocabulary therapy.
    """
    ctx = _get_common_context(request, lang)

    # Get core words from request or use defaults
    core_words = request.core_words or []
    if not core_words:
        # Default core words if none provided
        core_words = (
            ["더", "또", "아니", "네", "싫어", "줘", "이거", "저거", "뭐", "어디"]
            if lang == "ko"
            else ["more", "want", "no", "yes", "help", "go", "stop", "my", "that", "what"]
        )

    core_words_str = ", ".join(f'"{w}"' for w in core_words)

    if lang == "ko":
        return f"""당신은 아동 언어치료사를 돕는 전문 문장 생성 AI입니다.
핵심 어휘 치료를 위한 문장 {batch_size}개를 생성해주세요.

## 생성 조건

### 기본 정보
- 언어: 한국어
- 대상 아동 연령: {request.age}세
- {ctx['age_guideline']}

### 문장 구조 (매우 중요!)
- **tokens 배열의 길이가 정확히 {request.sentenceLength}개여야 합니다**
- 서버가 tokens를 join하여 문장을 만듭니다
- 목표 음소: '{request.target.phoneme}'
- 음소 위치: {ctx['position_desc']}

### 핵심 어휘 목록 (반드시 사용!)
{core_words_str}

### 치료 정보
- 진단명: {request.diagnosis.value}
- 치료 접근법: 핵심 어휘 접근법{ctx['theme_section']}{ctx['function_section']}

## 핵심 어휘 접근법 설명
- 위의 핵심 어휘 중 하나를 반드시 문장에 포함해야 합니다
- 핵심 어휘는 다양한 상황에서 자주 사용되는 기능어입니다
- 같은 핵심 어휘를 여러 다른 문맥에서 반복 사용하세요

## 중요 지침

1. **토큰 수 정확성**: 모든 문장의 tokens 배열은 정확히 {request.sentenceLength}개 요소를 가져야 합니다
2. **핵심 어휘 필수**: 각 문장에 위 목록의 핵심 어휘 중 하나가 반드시 포함되어야 합니다
3. **아동 적절성**: 긍정적이고 안전한 내용만 생성
4. **다양한 문맥**: 같은 핵심 어휘도 다양한 상황에서 사용

## 출력 형식

반드시 다음 JSON 형식으로만 출력하세요:
```json
{{"items": [
  {{
    "core_word": "줘",
    "tokens": ["우유", "좀", "줘"]
  }}
]}}
```

{batch_size}개 문장을 생성해주세요. JSON 출력만 허용됩니다."""

    else:
        return f"""You are a specialized AI assistant helping speech-language pathologists.
Please generate {batch_size} sentences for core vocabulary therapy.

## Generation Requirements

### Basic Information
- Language: English
- Target child age: {request.age} years old
- {ctx['age_guideline']}

### Sentence Structure (CRITICAL!)
- **The tokens array must have exactly {request.sentenceLength} elements**
- The server joins tokens to create the sentence
- Target phoneme: '{request.target.phoneme}'
- Phoneme position: {ctx['position_desc']}

### Core Vocabulary List (MUST USE!)
{core_words_str}

### Therapy Information
- Diagnosis: {request.diagnosis.value}
- Therapy approach: core vocabulary approach{ctx['theme_section']}{ctx['function_section']}

## Core Vocabulary Approach Explanation
- Each sentence MUST include one of the core words listed above
- Core words are high-frequency function words used across many contexts
- Use the same core word in multiple different contexts

## Important Guidelines

1. **Token count accuracy**: All sentence tokens arrays must have exactly {request.sentenceLength} elements
2. **Core word required**: Each sentence must include one core word from the list above
3. **Child appropriateness**: Only positive and safe content
4. **Varied contexts**: Use the same core word in different situations

## Output Format

Output MUST be in the following JSON format only:
```json
{{"items": [
  {{
    "core_word": "want",
    "tokens": ["I", "want", "more", "cookies"]
  }}
]}}
```

Generate {batch_size} sentences. JSON output only."""


def _generate_word_count_examples(word_count: int) -> str:
    """Generate examples showing correct word count.

    Args:
        word_count: The required number of words/어절.

    Returns:
        A string with examples of correct word counts.
    """
    examples = {
        2: [
            (["사과", "먹어요"], "request"),
            (["강아지", "귀여워"], "attention"),
        ],
        3: [
            (["고양이가", "밥을", "먹어요"], "request"),
            (["엄마가", "책을", "읽어요"], "attention"),
        ],
        4: [
            (["문", "좀", "닫아", "줘"], "request"),
            (["아빠가", "요리를", "하고", "있어요"], "attention"),
        ],
        5: [
            (["엄마가", "맛있는", "간식을", "만들어", "주었어요"], "request"),
            (["우리", "가족이", "함께", "공원에", "갔어요"], "attention"),
        ],
        6: [
            (["아빠가", "오늘", "저녁에", "맛있는", "음식을", "만들었어요"], "request"),
        ],
    }

    if word_count not in examples:
        return ""

    lines = [f"**{word_count}개 토큰 예시:**"]
    for tokens, func in examples[word_count]:
        tokens_json = str(tokens).replace("'", '"')
        lines.append(f'  - {{"tokens": {tokens_json}, "function": "{func}"}}')

    return "\n".join(lines)


def _build_korean_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build a Korean prompt for therapy sentence generation (default/fallback).

    Uses token-based output format.

    Args:
        request: The generation request.
        batch_size: Number of sentences to generate.

    Returns:
        A Korean prompt string.
    """
    ctx = _get_common_context(request, "ko")
    token_examples = _generate_word_count_examples(request.sentenceLength)

    prompt = f"""당신은 아동 언어치료사를 돕는 전문 문장 생성 AI입니다.
다음 조건에 맞는 한국어 치료 문장 {batch_size}개를 생성해주세요.

## 생성 조건

### 기본 정보
- 언어: 한국어
- 대상 아동 연령: {request.age}세
- {ctx['age_guideline']}

### 문장 구조 (매우 중요!)
- **tokens 배열의 길이가 정확히 {request.sentenceLength}개여야 합니다**
- 서버가 tokens를 join하여 문장을 만듭니다
- 목표 음소: '{request.target.phoneme}'
- 음소 위치: {ctx['position_desc']}
- 최소 출현 횟수: {request.target.minOccurrences}회 이상

{token_examples}

### 치료 정보
- 진단명: {request.diagnosis.value}
- 치료 접근법: {request.therapyApproach.value}{ctx['theme_section']}{ctx['function_section']}

## 중요 지침

1. **토큰 수 정확성 (가장 중요!)**: 모든 문장의 tokens 배열은 정확히 {request.sentenceLength}개 요소를 가져야 합니다
   - {request.sentenceLength - 1}개나 {request.sentenceLength + 1}개는 허용되지 않습니다
   - 생성 전에 토큰 수를 꼭 세어보세요

2. **아동 적절성**: 모든 문장은 아동에게 안전하고 적절한 내용이어야 합니다.
   - 폭력, 공포, 부정적 감정 표현 금지
   - 긍정적이고 밝은 내용 위주

3. **음소 정확성**: 목표 음소 '{request.target.phoneme}'이(가) 지정된 위치({ctx['position_desc']})에 {request.target.minOccurrences}회 이상 포함되어야 합니다.

4. **자연스러움**: 문장이 자연스럽고 일상에서 사용할 수 있는 표현이어야 합니다.

## 출력 형식

반드시 다음 JSON 형식으로만 출력하세요:
```json
{{"items": [
  {{"tokens": ["문", "좀", "닫아", "줘"], "function": "request"}},
  {{"tokens": ["엄마", "여기", "봐", "주세요"], "function": "attention"}}
]}}
```

{batch_size}개의 문장을 생성해주세요. JSON 출력만 허용됩니다."""

    return prompt


def _build_english_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build an English prompt for therapy sentence generation (default/fallback).

    Uses token-based output format.

    Args:
        request: The generation request.
        batch_size: Number of sentences to generate.

    Returns:
        An English prompt string.
    """
    ctx = _get_common_context(request, "en")

    prompt = f"""You are a specialized AI assistant helping speech-language pathologists generate therapy sentences.
Please generate {batch_size} English therapy sentences according to the following requirements.

## Generation Requirements

### Basic Information
- Language: English
- Target child age: {request.age} years old
- {ctx['age_guideline']}

### Sentence Structure (CRITICAL!)
- **The tokens array must have exactly {request.sentenceLength} elements**
- The server joins tokens to create the sentence
- Target phoneme: '{request.target.phoneme}'
- Phoneme position: {ctx['position_desc']}
- Minimum occurrences: {request.target.minOccurrences} or more

### Therapy Information
- Diagnosis: {request.diagnosis.value}
- Therapy approach: {request.therapyApproach.value}{ctx['theme_section']}{ctx['function_section']}

## Important Guidelines

1. **Token count accuracy (MOST IMPORTANT!)**: All sentence tokens arrays must have exactly {request.sentenceLength} elements
   - {request.sentenceLength - 1} or {request.sentenceLength + 1} elements are NOT allowed
   - Count the tokens before generating

2. **Child appropriateness**: All sentences must be safe and appropriate for children.
   - No violence, fear, or negative emotional content
   - Focus on positive and cheerful content

3. **Phoneme accuracy**: The target phoneme '{request.target.phoneme}' must appear in the specified position ({ctx['position_desc']}) at least {request.target.minOccurrences} time(s).

4. **Naturalness**: Sentences should be natural and usable in everyday situations.

## Output Format

Output MUST be in the following JSON format only:
```json
{{"items": [
  {{"tokens": ["Please", "help", "me", "now"], "function": "request"}},
  {{"tokens": ["Look", "at", "the", "cat"], "function": "attention"}}
]}}
```

Generate {batch_size} sentences. JSON output only."""

    return prompt
