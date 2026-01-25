"""Generate candidates tool for therapy sentence generation.

This module provides the generate_candidates function that uses an LLM
to generate candidate therapy sentences based on the given requirements.

Example:
    >>> from app.api.v2.schemas import GenerateRequestV2, Language, ...
    >>> request = GenerateRequestV2(language=Language.KO, age=5, ...)
    >>> result = await generate_candidates(request)
    >>> len(result.candidates) > 0
    True
"""

from dataclasses import dataclass
import json
import logging
import re
import time

from openai import AsyncOpenAI

from app.config import settings
from app.api.v2.schemas import DifficultyLevel, GenerateRequestV2
from app.services.prompt.builder import build_generation_prompt

logger = logging.getLogger(__name__)


_client: AsyncOpenAI | None = None
_ALLOWED_DIFFICULTIES = {level.value for level in DifficultyLevel}

# Gemini API base URL for OpenAI compatibility
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


@dataclass
class GenerateCandidatesResult:
    """Generated candidates with optional contrast sets."""

    candidates: list[dict]
    contrast_sets: list[dict] | None = None


def _get_client() -> AsyncOpenAI:
    """Get or create the Gemini client (via OpenAI compatibility layer).

    Uses lazy initialization to avoid creating the client
    until it's actually needed.

    Returns:
        AsyncOpenAI client instance configured for Gemini.

    Raises:
        ValueError: If Gemini API key is not configured.
    """
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is not configured")
        _client = AsyncOpenAI(
            api_key=settings.gemini_api_key,
            base_url=GEMINI_BASE_URL,
        )
    return _client


async def generate_candidates(
    request: GenerateRequestV2,
    batch_size: int | None = None,
) -> GenerateCandidatesResult:
    """Generate candidate therapy sentences using LLM.

    This function builds a prompt based on the generation request and
    calls the OpenAI API to generate candidate sentences. The generated
    sentences are then normalized and returned.

    Args:
        request: The generation request containing language, age, target
            phoneme, diagnosis, therapy approach, and other parameters.
        batch_size: Number of sentences to generate. Defaults to count * 3
            to provide enough candidates for filtering.

    Returns:
        GenerateCandidatesResult with candidates and optional contrast sets.
        Each candidate includes:
        - sentence: normalized sentence string
        - difficulty: optional difficulty level (when provided by the model)

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
        >>> result = await generate_candidates(request)
        >>> isinstance(result.candidates, list)
        True

    Raises:
        ValueError: If OpenAI API key is not configured.
        OpenAI API exceptions for network or API errors.
    """
    if batch_size is None:
        batch_size = request.count * 3

    prompt_start = time.time()
    prompt = build_generation_prompt(request, batch_size)
    prompt_time = int((time.time() - prompt_start) * 1000)
    prompt_len = len(prompt)

    client = _get_client()

    # Gemini 3 Flash with reasoning
    model = "gemini-3-flash-preview"
    logger.info(
        f"[LLM] 호출 시작 - model={model}, "
        f"prompt_len={prompt_len}, batch_size={batch_size}"
    )

    system_prompt = "You are a helpful assistant that generates therapy sentences for children. Always respond in valid JSON format."

    llm_start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            timeout=60.0,
        )
        llm_time = int((time.time() - llm_start) * 1000)
        logger.info(f"[LLM] 응답 수신 - {llm_time}ms")
    except Exception as e:
        llm_time = int((time.time() - llm_start) * 1000)
        logger.error(f"[LLM] API 호출 실패 - {llm_time}ms, error: {type(e).__name__}: {e}")
        raise

    content = response.choices[0].message.content
    if not content:
        logger.warning("[LLM] 빈 응답 수신")
        return GenerateCandidatesResult(candidates=[])

    response_len = len(content)
    logger.debug(f"[LLM] 응답 길이: {response_len} chars")

    parse_start = time.time()
    try:
        data = json.loads(content)
        sentences: list[dict] = []
        contrast_sets: list[dict] = []
        parse_format = "unknown"

        # 새로운 tokens 기반 형식: {"items": [...]}
        if "items" in data:
            parse_format = "items"
            for item in data["items"]:
                sentence = None
                if "tokens" in item and isinstance(item["tokens"], list):
                    sentence = " ".join(item["tokens"])
                elif "sentence" in item and isinstance(item["sentence"], str):
                    sentence = item["sentence"]
                elif "text" in item and isinstance(item["text"], str):
                    sentence = item["text"]

                if sentence:
                    candidate = {"sentence": sentence}
                    difficulty = item.get("difficulty")
                    if isinstance(difficulty, str) and difficulty in _ALLOWED_DIFFICULTIES:
                        candidate["difficulty"] = difficulty
                    sentences.append(candidate)
        # contrast 모드용 tokens 기반 형식: {"sets": [...]}
        elif "sets" in data:
            parse_format = "sets"
            for s in data["sets"]:
                target_sentence = _build_tokenized_sentence(s, "target_sentence")
                contrast_sentence = _build_tokenized_sentence(s, "contrast_sentence")

                if target_sentence:
                    sentences.append({"sentence": target_sentence["text"]})
                if contrast_sentence:
                    sentences.append({"sentence": contrast_sentence["text"]})

                if target_sentence and contrast_sentence:
                    contrast_sets.append(
                        {
                            "targetWord": _get_contrast_word(s, "target_word"),
                            "contrastWord": _get_contrast_word(s, "contrast_word"),
                            "targetSentence": target_sentence,
                            "contrastSentence": contrast_sentence,
                        }
                    )
        # 기존 형식 하위 호환: {"sentences": [...]}
        elif "sentences" in data:
            parse_format = "sentences"
            raw_sentences = data.get("sentences", [])
            if isinstance(raw_sentences, list):
                sentences = [{"sentence": s} for s in raw_sentences if isinstance(s, str)]

        parse_time = int((time.time() - parse_start) * 1000)
        logger.info(f"[LLM] 파싱 완료 - format={parse_format}, {len(sentences)}개, {parse_time}ms")

        # 샘플 로깅 (처음 3개)
        if sentences:
            samples = sentences[:3]
            logger.debug(f"[LLM] 샘플: {samples}")

        normalized = []
        for item in sentences:
            sentence = item.get("sentence")
            if not isinstance(sentence, str):
                continue
            normalized_item = {
                "sentence": _normalize_sentence(sentence),
            }
            difficulty = item.get("difficulty")
            if isinstance(difficulty, str) and difficulty in _ALLOWED_DIFFICULTIES:
                normalized_item["difficulty"] = difficulty
            normalized.append(normalized_item)
        if contrast_sets:
            _normalize_contrast_sets(contrast_sets)
        return GenerateCandidatesResult(candidates=normalized, contrast_sets=contrast_sets or None)
    except json.JSONDecodeError as e:
        parse_time = int((time.time() - parse_start) * 1000)
        logger.warning(f"[LLM] JSON 파싱 실패 - {parse_time}ms, error: {e}")
        logger.debug(f"[LLM] 원본 응답: {content[:500]}...")
        # Fallback: try to extract quoted strings
        matches = re.findall(r'"([^"]+)"', content)
        logger.info(f"[LLM] Fallback 파싱 - {len(matches)}개 추출")
        return GenerateCandidatesResult(
            candidates=[{"sentence": _normalize_sentence(m)} for m in matches]
        )


def _normalize_sentence(sentence: str) -> str:
    """Normalize a generated sentence.

    Removes leading/trailing whitespace, numbering prefixes,
    and surrounding quotes.

    Args:
        sentence: The raw sentence string to normalize.

    Returns:
        The normalized sentence string.

    Example:
        >>> _normalize_sentence('  1. "Hello world"  ')
        'Hello world'
        >>> _normalize_sentence("2) 안녕하세요")
        '안녕하세요'
    """
    s = sentence.strip()
    # Remove numbering like "1. " or "1) "
    s = re.sub(r"^\d+[\.\)]\s*", "", s)
    # Remove surrounding quotes
    s = s.strip("\"'")
    return s


def _build_tokenized_sentence(payload: dict, key: str) -> dict | None:
    """Build a TokenizedSentence-compatible dict from payload."""
    sentence = payload.get(key)
    if not isinstance(sentence, dict):
        return None

    tokens = sentence.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        return None

    cleaned_tokens = [str(token) for token in tokens if isinstance(token, (str, int, float))]
    if not cleaned_tokens:
        return None

    text = " ".join(cleaned_tokens)
    return {
        "text": text,
        "tokens": cleaned_tokens,
    }


def _get_contrast_word(payload: dict, key: str) -> str:
    if key in payload and isinstance(payload[key], str):
        return payload[key]
    camel_key = "".join([key.split("_")[0]] + [part.title() for part in key.split("_")[1:]])
    value = payload.get(camel_key)
    return value if isinstance(value, str) else ""


def _normalize_contrast_sets(contrast_sets: list[dict]) -> None:
    for contrast_set in contrast_sets:
        for sentence_key in ("targetSentence", "contrastSentence"):
            sentence = contrast_set.get(sentence_key)
            if isinstance(sentence, dict) and isinstance(sentence.get("text"), str):
                sentence["text"] = _normalize_sentence(sentence["text"])
