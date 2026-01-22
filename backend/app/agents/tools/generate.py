"""Generate candidates tool for therapy sentence generation.

This module provides the generate_candidates function that uses an LLM
to generate candidate therapy sentences based on the given requirements.

Example:
    >>> from app.api.v2.schemas import GenerateRequestV2, Language, ...
    >>> request = GenerateRequestV2(language=Language.KO, age=5, ...)
    >>> sentences = await generate_candidates(request)
    >>> len(sentences) > 0
    True
"""

import json
import logging
import re
import time

from openai import AsyncOpenAI

from app.config import settings
from app.api.v2.schemas import GenerateRequestV2
from app.services.prompt.builder import build_generation_prompt

logger = logging.getLogger(__name__)


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Get or create the OpenAI client.

    Uses lazy initialization to avoid creating the client
    until it's actually needed.

    Returns:
        AsyncOpenAI client instance.

    Raises:
        ValueError: If OpenAI API key is not configured.
    """
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is not configured")
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_candidates(
    request: GenerateRequestV2,
    batch_size: int | None = None,
) -> list[str]:
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
        A list of generated and normalized sentences.

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
        >>> sentences = await generate_candidates(request)
        >>> isinstance(sentences, list)
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

    # GPT-5.2 Responses API
    # core_vocabulary는 복잡한 조건이 많으므로 medium effort 사용
    from app.api.v2.schemas import TherapyApproach

    reasoning_effort = "low"
    if request.therapyApproach == TherapyApproach.CORE_VOCABULARY:
        reasoning_effort = "medium"

    logger.info(
        f"[LLM] 호출 시작 - model=gpt-5.2, effort={reasoning_effort}, "
        f"prompt_len={prompt_len}, batch_size={batch_size}"
    )

    system_prompt = "You are a helpful assistant that generates therapy sentences for children. Always respond in valid JSON format."

    llm_start = time.time()
    try:
        response = await client.responses.create(
            model="gpt-5.2",
            input=f"{system_prompt}\n\n{prompt}",
            reasoning={"effort": reasoning_effort},
            text={"format": {"type": "json_object"}},
            timeout=120.0,  # 2분 타임아웃 (medium reasoning은 시간이 더 필요)
        )
        llm_time = int((time.time() - llm_start) * 1000)
        logger.info(f"[LLM] 응답 수신 - {llm_time}ms")
    except Exception as e:
        llm_time = int((time.time() - llm_start) * 1000)
        logger.error(f"[LLM] API 호출 실패 - {llm_time}ms, error: {type(e).__name__}: {e}")
        raise

    content = response.output_text
    if not content:
        logger.warning("[LLM] 빈 응답 수신")
        return []

    response_len = len(content)
    logger.debug(f"[LLM] 응답 길이: {response_len} chars")

    parse_start = time.time()
    try:
        data = json.loads(content)
        sentences = []
        parse_format = "unknown"

        # 새로운 tokens 기반 형식: {"items": [...]}
        if "items" in data:
            parse_format = "items"
            for item in data["items"]:
                if "tokens" in item and isinstance(item["tokens"], list):
                    sentences.append(" ".join(item["tokens"]))
        # contrast 모드용 tokens 기반 형식: {"sets": [...]}
        elif "sets" in data:
            parse_format = "sets"
            for s in data["sets"]:
                if "target_sentence" in s and "tokens" in s["target_sentence"]:
                    sentences.append(" ".join(s["target_sentence"]["tokens"]))
                if "contrast_sentence" in s and "tokens" in s["contrast_sentence"]:
                    sentences.append(" ".join(s["contrast_sentence"]["tokens"]))
        # 기존 형식 하위 호환: {"sentences": [...]}
        elif "sentences" in data:
            parse_format = "sentences"
            raw_sentences = data.get("sentences", [])
            if isinstance(raw_sentences, list):
                sentences = [s for s in raw_sentences if isinstance(s, str)]

        parse_time = int((time.time() - parse_start) * 1000)
        logger.info(f"[LLM] 파싱 완료 - format={parse_format}, {len(sentences)}개, {parse_time}ms")

        # 샘플 로깅 (처음 3개)
        if sentences:
            samples = sentences[:3]
            logger.debug(f"[LLM] 샘플: {samples}")

        return [_normalize_sentence(s) for s in sentences if isinstance(s, str)]
    except json.JSONDecodeError as e:
        parse_time = int((time.time() - parse_start) * 1000)
        logger.warning(f"[LLM] JSON 파싱 실패 - {parse_time}ms, error: {e}")
        logger.debug(f"[LLM] 원본 응답: {content[:500]}...")
        # Fallback: try to extract quoted strings
        matches = re.findall(r'"([^"]+)"', content)
        logger.info(f"[LLM] Fallback 파싱 - {len(matches)}개 추출")
        return [_normalize_sentence(m) for m in matches]


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
