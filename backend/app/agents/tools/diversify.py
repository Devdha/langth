"""다양성 보장 도구.

유사한 문장이 너무 많이 선택되지 않도록 결과의 다양성을 보장합니다.
"""

from collections import defaultdict
import re

from app.agents.tools.score import ScoredSentence


def diversify_results(
    scored: list[ScoredSentence],
    count: int,
    max_similar: int = 2,
) -> list[ScoredSentence]:
    """다양성을 보장하며 최종 결과를 선택합니다.

    동일한 패턴(첫 번째 매칭 단어 기준)을 가진 문장은 max_similar 개수까지만
    선택되며, 점수가 높은 순서로 선택됩니다.

    Args:
        scored: 점수순 정렬된 문장들
        count: 선택할 개수
        max_similar: 유사 문장 최대 개수 (기본: 2)

    Returns:
        다양성이 보장된 ScoredSentence 리스트

    Examples:
        >>> from app.agents.tools.score import ScoredSentence
        >>> scored = [
        ...     ScoredSentence("라면이 맛있어요", ["라면이"], 4, 85.0, {}),
        ...     ScoredSentence("라면을 먹어요", ["라면을"], 4, 80.0, {}),
        ...     ScoredSentence("달리기 좋아요", ["달리기"], 4, 75.0, {}),
        ... ]
        >>> results = diversify_results(scored, count=2, max_similar=1)
        >>> len(results)
        2
    """
    if len(scored) <= count:
        return scored

    selected: list[ScoredSentence] = []
    selected_indexes: set[int] = set()
    pattern_counts: dict[str, int] = defaultdict(int)
    start_counts: dict[str, int] = defaultdict(int)
    ending_counts: dict[str, int] = defaultdict(int)
    difficulty_counts: dict[str, int] = defaultdict(int)

    # 난이도별 목표 개수 계산 (균등 분배)
    target_per_difficulty = count // 3 if count >= 3 else 1

    # 후보별 다양성 키 사전 계산
    candidate_keys = []
    for sentence in scored:
        candidate_keys.append(
            {
                "pattern": _get_pattern(sentence),
                "start": _get_start_key(sentence),
                "ending": _get_ending_key(sentence),
                "difficulty": sentence.difficulty or "unknown",
            }
        )

    # 다양성 페널티를 반영한 그리디 선택
    for _ in range(count):
        best_idx = None
        best_adjusted_score = None

        for idx, sentence in enumerate(scored):
            if idx in selected_indexes:
                continue

            keys = candidate_keys[idx]
            if pattern_counts[keys["pattern"]] >= max_similar:
                continue

            # 반복되는 시작어/종결형에 페널티 부여
            penalty = (
                start_counts[keys["start"]] * 3
                + ending_counts[keys["ending"]] * 4
            )

            # 난이도 균형 페널티: 목표를 초과하면 큰 페널티
            diff_count = difficulty_counts[keys["difficulty"]]
            if diff_count >= target_per_difficulty:
                penalty += (diff_count - target_per_difficulty + 1) * 10

            adjusted_score = sentence.score - penalty

            if best_idx is None or adjusted_score > best_adjusted_score:
                best_idx = idx
                best_adjusted_score = adjusted_score

        if best_idx is None:
            break

        selected_indexes.add(best_idx)
        selected.append(scored[best_idx])

        keys = candidate_keys[best_idx]
        pattern_counts[keys["pattern"]] += 1
        start_counts[keys["start"]] += 1
        ending_counts[keys["ending"]] += 1
        difficulty_counts[keys["difficulty"]] += 1

    # 부족하면 남은 것 중 추가
    if len(selected) < count:
        for idx, sentence in enumerate(scored):
            if idx in selected_indexes:
                continue
            selected.append(sentence)
            if len(selected) >= count:
                break

    return selected


def _get_pattern(sentence: ScoredSentence) -> str:
    """문장의 패턴 키 추출.

    첫 번째 매칭 단어의 앞 2글자를 패턴으로 사용합니다.
    매칭 단어가 없으면 문장 첫 단어의 앞 2글자를 사용합니다.

    Args:
        sentence: 점수가 부여된 문장

    Returns:
        패턴 키 문자열
    """
    if sentence.matched_words:
        # 매칭 단어를 패턴으로 (조사/기호 제거)
        first_match = sentence.matched_words[0]
        return _normalize_token(first_match)

    # 매칭 단어 없으면 문장 첫 단어
    words = sentence.sentence.split()
    if words:
        return _normalize_token(words[0])

    return ""


def _get_start_key(sentence: ScoredSentence) -> str:
    """문장 시작 패턴 키 추출.

    Args:
        sentence: 점수가 부여된 문장

    Returns:
        시작 패턴 키 문자열
    """
    words = sentence.sentence.split()
    if not words:
        return ""
    return _normalize_token(words[0])


def _get_ending_key(sentence: ScoredSentence) -> str:
    """문장 종결 패턴 키 추출.

    Args:
        sentence: 점수가 부여된 문장

    Returns:
        종결 패턴 키 문자열
    """
    text = sentence.sentence.strip()
    if not text:
        return ""

    if text.endswith("?"):
        return "?"
    if text.endswith("!"):
        return "!"

    text = text.rstrip(".")
    words = text.split()
    last_word = words[-1] if words else text

    for ending in _COMMON_ENDINGS:
        if last_word.endswith(ending):
            return ending

    normalized = re.sub(r"[^0-9A-Za-z가-힣]", "", last_word)
    if not normalized:
        return ""
    return normalized[-2:] if len(normalized) >= 2 else normalized


_COMMON_ENDINGS = [
    "해주세요",
    "주세요",
    "할까요",
    "까요",
    "했어요",
    "했어",
    "해요",
    "어요",
    "아요",
    "네요",
    "세요",
    "죠",
    "요",
    "다",
]


def _normalize_token(token: str) -> str:
    """패턴 비교용 토큰 정규화.

    Args:
        token: 원본 토큰

    Returns:
        정규화된 토큰
    """
    cleaned = re.sub(r"[^0-9A-Za-z가-힣]", "", token)
    if not cleaned:
        return ""

    if _contains_korean(cleaned):
        return _strip_korean_particles(cleaned)
    return cleaned.lower()


def _contains_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


_KOREAN_PARTICLES = [
    "이랑",
    "랑",
    "으로",
    "로",
    "까지",
    "부터",
    "처럼",
    "같이",
    "에게",
    "께",
    "한테",
    "에서",
    "에게서",
    "으로부터",
    "와",
    "과",
    "이",
    "가",
    "을",
    "를",
    "은",
    "는",
    "에",
    "도",
    "만",
]


def _strip_korean_particles(word: str) -> str:
    for particle in _KOREAN_PARTICLES:
        if word.endswith(particle) and len(word) > len(particle):
            return word[: -len(particle)]
    return word
