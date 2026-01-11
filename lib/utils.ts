/**
 * 문장의 어절 수를 계산합니다.
 * 띄어쓰기 기준으로 분리하여 계산합니다.
 */
export function countWords(sentence: string): number {
  // 공백 문자로 분리
  const words = sentence.trim().split(/\s+/);
  // 빈 문자열이나 공백만 있는 경우 처리
  if (words.length === 1 && words[0] === '') {
    return 0;
  }
  return words.length;
}

/**
 * 문장이 특정 어절 수 조건을 만족하는지 확인합니다.
 */
export function hasCorrectWordCount(sentence: string, targetCount: number): boolean {
  return countWords(sentence) === targetCount;
}

/**
 * 음소가 문장에 포함되어 있는지 확인합니다.
 * 한글: 초성, 종성 모두 검사
 * 영어: 대소문자 무시하고 문자 포함 여부 검사
 */
export function hasTargetPhoneme(sentence: string, targetPhoneme: string, language: string = 'ko'): boolean {
  if (!targetPhoneme) return true;

  // 영어인 경우 단순 포함 검사
  if (language === 'en') {
    return sentence.toLowerCase().includes(targetPhoneme.toLowerCase());
  }

  // 한글인 경우 초성/종성 분해 검사
  const CHOSUNG = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
  const JONGSUNG = ['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];

  for (const char of sentence) {
    const code = char.charCodeAt(0);
    // 한글 음절 범위: 0xAC00 ~ 0xD7A3
    if (code >= 0xAC00 && code <= 0xD7A3) {
      const offset = code - 0xAC00;
      const chosungIndex = Math.floor(offset / (21 * 28));
      const jongsungIndex = offset % 28;

      // 초성 검사
      if (CHOSUNG[chosungIndex] === targetPhoneme) return true;
      // 종성 검사 (복합 종성도 포함)
      if (JONGSUNG[jongsungIndex].includes(targetPhoneme)) return true;
    }
  }
  return false;
}

/**
 * 문장 리스트를 필터링하여 조건에 맞는 항목만 반환합니다.
 */
export function filterSentences(
  sentences: string[],
  targetWordCount: number,
  targetPhoneme: string,
  language: string = 'ko'
): string[] {
  return sentences.filter(sentence => {
    const wordCountMatch = hasCorrectWordCount(sentence, targetWordCount);
    const phonemeMatch = hasTargetPhoneme(sentence, targetPhoneme, language);
    return wordCountMatch && phonemeMatch;
  });
}

/**
 * 유일한 ID 생성 함수
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
