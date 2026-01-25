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
from app.services.lexical.core_vocabulary import resolve_core_words

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

# Age-appropriate guidelines with specific examples and vocabulary constraints
AGE_GUIDELINES: dict[int, dict[str, str]] = {
    3: {
        "ko": """3세 (영유아):
  - 어휘: 엄마, 아빠, 물, 밥, 까까, 맘마, 응가, 쉬, 아파, 뜨거, 잠, 공, 차, 멍멍, 야옹
  - 문장 형태: 1-2단어 조합 또는 매우 짧은 문장
  - 특징: 의성어/의태어 적극 활용 (멍멍, 야옹, 부릉, 콩콩, 쿵쿵)
  - 조사: 생략 가능 ("밥 줘", "물 더")
  - 예시: "밥 줘", "엄마 봐", "멍멍 왔어", "까까 더"
  - 금지: 수영장, 창문, 장난감 같은 복잡한 단어 사용 금지""",
        "en": """3 years (toddler):
  - Vocabulary: mama, dada, water, milk, ball, car, doggy, kitty, owie, hot, no, more
  - Sentence form: 1-2 word combinations or very short sentences
  - Features: Use onomatopoeia (woof, meow, vroom, boom)
  - Example: "more milk", "mama look", "doggy there"
  - Avoid: complex words like swimming pool, window, playground""",
    },
    4: {
        "ko": """4세 (유아 초기):
  - 어휘: 기본 가족(엄마, 아빠, 동생), 음식(사과, 바나나, 우유), 동물(강아지, 고양이, 토끼)
  - 문장 형태: 간단한 주어+서술어 또는 주어+목적어+서술어
  - 특징: 기본 조사 사용 가능 (-가, -를, -에)
  - 예시: "강아지가 와요", "사과 먹어", "엄마 여기 있어"
  - 금지: 추상적 개념, 복잡한 시간 표현""",
        "en": """4 years (early preschool):
  - Vocabulary: basic family (mom, dad, baby), food (apple, cookie, juice), animals (dog, cat, bird)
  - Sentence form: simple subject+verb or subject+object+verb
  - Features: basic prepositions (in, on, at)
  - Example: "doggy is here", "I want apple", "mommy help"
  - Avoid: abstract concepts, complex time expressions""",
    },
    5: {
        "ko": """5세 (유아 중기):
  - 어휘: 확장된 명사(유치원, 친구, 선생님), 동사(만들다, 그리다, 달리다)
  - 문장 형태: 기본 문장, 조사 정확히 사용
  - 특징: -고, -서 등 간단한 연결어미 사용 가능
  - 예시: "친구랑 놀고 싶어", "선생님이 책 읽어줬어", "유치원에서 그림 그렸어"
  - 금지: 복잡한 종속절, 피동/사동 표현""",
        "en": """5 years (mid preschool):
  - Vocabulary: expanded nouns (school, friend, teacher), verbs (make, draw, run)
  - Sentence form: basic sentences with proper grammar
  - Features: simple conjunctions (and, because)
  - Example: "I want to play with friend", "teacher read the book"
  - Avoid: complex subordinate clauses, passive voice""",
    },
    6: {
        "ko": """6세 (유아 후기):
  - 어휘: 다양한 명사, 형용사, 부사 사용 가능
  - 문장 형태: 복합 문장, 시제 표현 가능
  - 특징: -면, -니까 등 조건/이유 표현 가능
  - 예시: "비가 오면 우산 써야 해", "배고프니까 밥 먹자", "어제 공원에서 놀았어"
  - 허용: 과거/미래 시제, 간단한 비유""",
        "en": """6 years (late preschool):
  - Vocabulary: varied nouns, adjectives, adverbs
  - Sentence form: compound sentences, tense expressions
  - Features: conditional/reason expressions (if, because, when)
  - Example: "If it rains, we need umbrella", "I played at the park yesterday"
  - Allowed: past/future tense, simple metaphors""",
    },
    7: {
        "ko": """7세 (학령기 진입):
  - 어휘: 학교 관련 어휘, 추상적 개념 가능
  - 문장 형태: 복잡한 문장 구조 가능
  - 특징: 비유, 추론, 가정 표현 가능
  - 예시: "만약 내가 새라면 하늘을 날 텐데", "그 이야기는 슬프지만 감동적이야"
  - 허용: 피동/사동, 관형절, 추상적 표현""",
        "en": """7 years (school entry):
  - Vocabulary: school-related words, abstract concepts allowed
  - Sentence form: complex sentence structures
  - Features: metaphors, inferences, hypothetical expressions
  - Example: "If I were a bird, I would fly", "The story is sad but touching"
  - Allowed: passive voice, relative clauses, abstract expressions""",
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


def _get_contrast_explanation_ko(approach_value: str) -> str:
    """Get Korean explanation for contrast-based therapy approach.

    Returns appropriate phonological feature constraints for
    minimal pairs vs maximal oppositions.

    Note: This function is preserved for future use in a separate
    word-pair discrimination mode.
    """
    if approach_value == "minimal_pairs":
        return """- **최소대립쌍**: 단 하나의 음운 자질만 다른 단어 쌍을 생성합니다
- 음운 자질: 조음위치, 조음방법, 기식성/긴장성 중 **하나만** 달라야 합니다
- 올바른 예시:
  - 'ㄱ' vs 'ㅋ' (기식성만 다름) → '감' vs '캄'
  - 'ㄱ' vs 'ㄷ' (조음위치만 다름) → '공' vs '동'
  - 'ㄴ' vs 'ㅁ' (조음위치만 다름) → '눈' vs '뭄'
  - 'ㄹ' vs 'ㄴ' (조음방법만 다름) → '라면' vs '나면'
- 잘못된 예시 (여러 자질이 다름):
  - 'ㄱ' vs 'ㅁ' ❌ (조음위치 + 조음방법 모두 다름)
  - 'ㅂ' vs 'ㄹ' ❌ (조음위치 + 조음방법 모두 다름)"""
    else:  # MAXIMAL_OPPOSITIONS
        return """- **최대대립**: 여러 음운 자질이 다른 단어 쌍을 생성합니다
- 음운 자질: 조음위치, 조음방법, 기식성/긴장성 중 **2개 이상** 달라야 합니다
- 올바른 예시:
  - 'ㄱ' vs 'ㅁ' (조음위치 + 조음방법 다름) → '곰' vs '몸'
  - 'ㅂ' vs 'ㄹ' (조음위치 + 조음방법 다름) → '밤' vs '람'
  - 'ㅅ' vs 'ㅁ' (조음위치 + 조음방법 다름) → '손' vs '몬'
  - 'ㅈ' vs 'ㄴ' (조음위치 + 조음방법 다름) → '잔' vs '난'
- 잘못된 예시 (하나의 자질만 다름):
  - 'ㄱ' vs 'ㅋ' ❌ (기식성만 다름 - 최소대립쌍임)
  - 'ㄴ' vs 'ㅁ' ❌ (조음위치만 다름 - 최소대립쌍임)"""


def _get_contrast_explanation_en(approach_value: str) -> str:
    """Get English explanation for contrast-based therapy approach.

    Returns appropriate phonological feature constraints for
    minimal pairs vs maximal oppositions.

    Note: This function is preserved for future use in a separate
    word-pair discrimination mode.
    """
    if approach_value == "minimal_pairs":
        return """- **Minimal pairs**: Generate word pairs that differ by ONLY ONE phonological feature
- Features: place, manner, or voicing - only **ONE** should differ
- Correct examples:
  - /p/ vs /b/ (voicing only) → 'pat' vs 'bat'
  - /t/ vs /d/ (voicing only) → 'tin' vs 'din'
  - /s/ vs /z/ (voicing only) → 'sip' vs 'zip'
  - /k/ vs /g/ (voicing only) → 'coat' vs 'goat'
  - /f/ vs /v/ (voicing only) → 'fan' vs 'van'
- Incorrect examples (multiple features differ):
  - /p/ vs /n/ ❌ (place + manner both differ)
  - /s/ vs /m/ ❌ (place + manner both differ)"""
    else:  # MAXIMAL_OPPOSITIONS
        return """- **Maximal oppositions**: Generate word pairs that differ by MULTIPLE phonological features
- Features: place, manner, AND/OR voicing - **2 or more** should differ
- Correct examples:
  - /p/ vs /n/ (place + manner differ) → 'pat' vs 'nat'
  - /s/ vs /m/ (place + manner differ) → 'sun' vs 'mum'
  - /f/ vs /n/ (place + manner differ) → 'fun' vs 'nun'
  - /k/ vs /m/ (place + manner differ) → 'cap' vs 'map'
- Incorrect examples (only one feature differs):
  - /p/ vs /b/ ❌ (voicing only - this is a minimal pair)
  - /t/ vs /d/ ❌ (voicing only - this is a minimal pair)"""


def build_generation_prompt(request: GenerateRequestV2, batch_size: int) -> str:
    """Build a prompt for therapy sentence generation.

    Constructs a language-specific prompt based on the generation request
    parameters, including diagnosis type, therapy approach, and optional
    communicative function.

    Routes to different prompt builders based on therapy approach:
    - complexity -> _build_complexity_prompt
    - core_vocabulary -> _build_core_vocab_prompt

    Note: minimal_pairs/maximal_oppositions are planned for a separate
    word-pair discrimination mode (not sentence generation).

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
        ...     therapyApproach=TherapyApproach.COMPLEXITY,
        ... )
        >>> prompt = build_generation_prompt(request, batch_size=30)
        >>> "한국어" in prompt
        True
    """
    lang = "ko" if request.language == Language.KO else "en"

    # Route based on therapy approach
    if request.therapyApproach == TherapyApproach.COMPLEXITY:
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
    # target이 None일 수 있음 (core_vocabulary)
    position_desc = ""
    if request.target:
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


def _get_example_tokens(token_count: int, phoneme: str, lang: str) -> str:
    """Get example tokens array matching the token count and phoneme.

    Args:
        token_count: The required number of tokens.
        phoneme: The target phoneme.
        lang: Language code ("ko" or "en").

    Returns:
        A JSON array string with example tokens.
    """
    en_examples = {
        2: '["Cat", "runs"]',
        3: '["The", "cat", "runs"]',
        4: '["The", "cat", "runs", "fast"]',
        5: '["The", "big", "cat", "runs", "fast"]',
        6: '["The", "big", "cat", "runs", "very", "fast"]',
    }
    ko_examples = {
        2: '["고양이가", "뛰어요"]',
        3: '["고양이가", "빨리", "뛰어요"]',
        4: '["귀여운", "고양이가", "빨리", "뛰어요"]',
        5: '["귀여운", "고양이가", "아주", "빨리", "뛰어요"]',
        6: '["귀여운", "작은", "고양이가", "아주", "빨리", "뛰어요"]',
    }
    examples = ko_examples if lang == "ko" else en_examples
    return examples.get(token_count, en_examples[3])


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

    Note: This function is preserved for future use in a separate
    word-pair discrimination mode. Currently not called.

    Args:
        request: The generation request.
        batch_size: Number of contrast pairs to generate.
        lang: Language code ("ko" or "en").

    Returns:
        A prompt string for contrast-based therapy.
    """
    ctx = _get_common_context(request, lang)
    # Use string value for approach comparison (enum removed from TherapyApproach)
    approach_value = request.therapyApproach.value
    approach_name = "최소대립쌍" if approach_value == "minimal_pairs" else "최대대립"
    approach_name_en = (
        "minimal pairs" if approach_value == "minimal_pairs" else "maximal oppositions"
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
{_get_contrast_explanation_ko(approach_value)}
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
{_get_contrast_explanation_en(approach_value)}
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
음운 환경의 복잡도에 따라 난이도가 결정됩니다:

**easy** - 단순한 음운 환경:
- 어두 초성 + 모음: "라면", "노래"
- 단순 음절 구조: CV, CVC
- 예: "라면 먹어요", "노래해요"

**medium** - 약간 복잡한 환경:
- 어중 위치: "우리", "머리"
- 겹받침 앞/뒤: "닭", "읽다"
- 예: "우리 집이에요", "머리 빗어요"

**hard** - 복잡한 음운 환경:
- 자음 연쇄: "쓸쓸", "글씨"
- 여러 번 출현: "라라라", "달려라"
- 예: "글씨를 써요", "달려가요"

**필수 요구사항**:
- 약 1/3 easy, 1/3 medium, 1/3 hard 비율로 생성
- {batch_size}개 문장: ~{batch_size//3} easy, ~{batch_size//3} medium, ~{batch_size//3} hard
- 특정 난이도에 치우치지 마세요

## 피해야 할 패턴 (매우 중요!)

아래 패턴은 절대 생성하지 마세요:

❌ **어른 말투**: "라면이 너무 맛있어요", "사과가 정말 달콤합니다"
   → 아이는 "라면 맛있어!", "사과 달아~"처럼 말합니다

❌ **의미 반복**: "맛있는 라면을 맛있게 먹어요", "예쁜 꽃이 예뻐요"
   → 같은 어근(맛있-, 예쁘-)이 반복되면 안 됩니다

❌ **맥락 없는 문장**: "라면을 먹어요", "공을 던져요"
   → 누가? 왜? 맥락이 있어야 합니다

❌ **같은 구조 반복**: "~가 ~를 ~해요" 패턴만 사용
   → 다양한 문장 구조를 사용하세요

❌ **명사구만**: "엄마 마음", "맛있는 소시지 세 개"
   → 서술어(동사/형용사)가 반드시 포함되어야 합니다
   → 짧은 문장도 완전한 문장이어야 함: "밥 줘", "엄마 봐"

## 좋은 문장 예시

✅ **자연스러운 아이 말투**:
- "엄마, 라면 먹고 싶어!" (요청 + 호칭)
- "우와, 라면이다!" (감탄)
- "이거 라면이야?" (질문)
- "라면 다 먹었어~" (보고)

✅ **다양한 문장 구조**:
- 요청문: "라면 주세요", "라면 먹을래"
- 질문문: "라면 맛있어?", "라면 뜨거워?"
- 감탄문: "라면 냄새 좋다!", "라면 맛있다~"
- 서술문: "나 라면 좋아해", "라면 다 먹었어"

✅ **짧은 문장도 완전한 문장으로** (2-3토큰):
- 2토큰: "밥 줘", "엄마 봐", "이거 뭐야?", "라면 맛있어!"
- 3토큰: "나 배고파", "엄마 어디야?", "이거 내 거야"
- ❌ 틀린 예: "엄마 마음" (명사구), "맛있는 라면" (명사구)

## 중요 지침

1. **토큰 수 정확성**: 모든 문장의 tokens 배열은 정확히 {request.sentenceLength}개 요소를 가져야 합니다
2. **난이도 분포**: easy, medium, hard를 균등하게 분배
3. **아동 적절성**: 긍정적이고 안전한 내용만 생성
4. **target_analysis**: 목표 음소가 어떤 음운 환경에서 나타나는지 설명
5. **다양성**: 문장 구조와 어휘를 다양하게 사용하세요

## 출력 형식

반드시 다음 JSON 형식으로만 출력하세요:
```json
{{"items": [
  {{
    "tokens": ["엄마,", "라면", "먹고", "싶어!"],
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
Difficulty is determined by phonological environment complexity:

**easy** - Target phoneme in simple, isolated position:
- Word-initial before vowel: "sun", "red", "kite"
- Word-final after vowel: "bus", "car", "book"
- Simple CVC words: "sit", "run", "cat"

**medium** - Target phoneme in simple consonant blends:
- Two-consonant blends: "sleep", "blue", "green", "stop"
- Initial blends: "bring", "slide", "clap"

**hard** - Target phoneme in complex clusters or challenging environments:
- Three-consonant clusters: "string", "spring", "splash"
- Medial clusters: "faster", "sister"
- Multiple occurrences: "scissors", "rooster"

**CRITICAL REQUIREMENT**:
- Generate approximately 1/3 easy, 1/3 medium, 1/3 hard sentences
- For {batch_size} sentences: ~{batch_size//3} easy, ~{batch_size//3} medium, ~{batch_size//3} hard
- Do NOT bias towards any single difficulty level

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
    "tokens": {_get_example_tokens(request.sentenceLength, request.target.phoneme if request.target else "K", "en")},
    "difficulty": "easy",
    "target_analysis": {{
      "phoneme": "{request.target.phoneme if request.target else 'K'}",
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
    core_words = resolve_core_words(lang, request.core_words)

    core_words_str = ", ".join(f'"{w}"' for w in core_words)

    if lang == "ko":
        return f"""아동 언어치료용 문장 {batch_size}개를 생성하세요.

## 핵심 규칙

1. **핵심 어휘 필수**: 모든 문장에 아래 단어 중 하나 포함
   {core_words_str}

2. **토큰 수**: 정확히 {request.sentenceLength}개

3. **자연스러운 문장**: 아이가 실제로 말할 법한 표현

## 대상
- {request.age}세 아동
- {ctx['age_guideline']}
{ctx['theme_section']}{ctx['function_section']}

## 피해야 할 패턴 (매우 중요!)

❌ **어른 말투**: "물을 마시고 싶습니다", "간식을 주세요"
   → 아이는 "물 줘!", "까까 줘~"처럼 말합니다

❌ **의미 반복**: "더 더 줘", "싫어 싫어"
   → 같은 단어가 반복되면 안 됩니다

❌ **맥락 없는 문장**: "줘", "싫어"
   → 뭘? 왜? 맥락이 있어야 합니다

❌ **같은 구조 반복**: "~를 ~해요" 패턴만 사용
   → 다양한 문장 구조를 사용하세요

❌ **명사구만**: "엄마 손", "맛있는 까까"
   → 서술어가 반드시 포함되어야 합니다
   → 짧아도 완전한 문장: "손 잡아", "까까 줘"

## 좋은 예시

✅ **자연스러운 아이 말투**:
- ["엄마,", "물", "줘"] (요청 + 호칭)
- ["까까", "더", "줘!"] (요청)
- ["이거", "뭐야?"] (질문)
- ["싫어,", "안", "해!"] (거부)

✅ **다양한 문장 구조**:
- 요청: "엄마 물 줘", "이거 줘"
- 질문: "이거 뭐야?", "어디 가?"
- 거부: "싫어!", "안 해"
- 감탄: "우와, 이거 봐!"

## 나쁜 예시 (금지)
- ["아니", "응가", "아니"] - 의미 없음
- ["멍멍", "야옹", "삐약"] - 의성어만 나열
- ["고양이가", "밥", "먹어요"] - 핵심 어휘 없음
- ["물을", "마시고", "싶어요"] - 어른 말투

## 출력 형식 (JSON만)
{{"items": [{{"core_word": "줘", "tokens": ["엄마,", "물", "줘"]}}]}}"""

    else:
        return f"""Generate {batch_size} therapy sentences for children.

## Core Rules

1. **Core word required**: Every sentence must include one of:
   {core_words_str}

2. **Token count**: Exactly {request.sentenceLength} tokens

3. **Natural sentences**: What a child would actually say

## Target
- {request.age} year old child
- {ctx['age_guideline']}
{ctx['theme_section']}{ctx['function_section']}

## Good examples
- ["I", "want", "more"] (want included)
- ["Please", "help", "me"] (help included)
- ["No", "thank", "you"] (no included)

## Bad examples (forbidden)
- ["The", "cat", "runs"] - no core word
- ["Birds", "fly", "high"] - no core word

## Output format (JSON only)
{{"items": [{{"core_word": "want", "tokens": ["I", "want", "more"]}}]}}"""


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
