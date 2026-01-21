"""다양성 보장 도구.

유사한 문장이 너무 많이 선택되지 않도록 결과의 다양성을 보장합니다.
"""

from collections import defaultdict

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
    """문장의 패턴 키 추출.

    첫 번째 매칭 단어의 앞 2글자를 패턴으로 사용합니다.
    매칭 단어가 없으면 문장 첫 단어의 앞 2글자를 사용합니다.

    Args:
        sentence: 점수가 부여된 문장

    Returns:
        패턴 키 문자열
    """
    if sentence.matched_words:
        # 매칭 단어의 첫 2글자를 패턴으로
        first_match = sentence.matched_words[0]
        return first_match[:2] if len(first_match) >= 2 else first_match

    # 매칭 단어 없으면 문장 첫 단어
    words = sentence.sentence.split()
    if words:
        return words[0][:2] if len(words[0]) >= 2 else words[0]

    return ""
