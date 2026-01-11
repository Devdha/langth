import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/**
 * 주제별로 프롬프트에 사용할 설명을 반환합니다.
 */
function getThemePrompt(theme: string, language: string): string {
  if (language === 'en') {
    const themes: Record<string, string> = {
      daily: 'Daily life situations (e.g., at home, during meals, playing)',
      food: 'Food-related sentences (e.g., favorite foods, eating, cooking)',
      animal: 'Animal-related sentences (e.g., dogs, cats, animal stories)',
      family: 'Family-related sentences (e.g., mom, dad, siblings, grandparents)',
    };
    return themes[theme] || 'Daily life situations';
  }

  const themes: Record<string, string> = {
    daily: '일상생활 상황에서 사용하는 문장들 (예: 집에서, 식사할 때, 놀 때)',
    food: '음식과 관련된 문장들 (예: 좋아하는 음식, 먹는 상황, 요리할 때)',
    animal: '동물과 관련된 문장들 (예: 강아지, 고양이, 동물 이야기)',
    family: '가족과 관련된 문장들 (예: 엄마, 아빠, 형제, 할머니 할아버지)',
  };

  return themes[theme] || '일상적인 상황에서 사용하는 문장들';
}

/**
 * 연령별 어휘 가이드라인을 반환합니다.
 */
function getAgeGuideline(age: number, language: string): string {
  if (language === 'en') {
    const guidelines: Record<number, string> = {
      3: 'Use very simple words a 3-year-old knows: basic verbs (eat, sleep, go, come), family words (mom, dad), body parts, simple objects',
      4: 'Use vocabulary appropriate for 4-year-olds: basic emotions, colors, numbers 1-10, simple location words (here, there, up, down)',
      5: 'Use vocabulary appropriate for 5-year-olds: time concepts (today, tomorrow), comparison words (big/small), simple connectors',
      6: 'Use vocabulary appropriate for 6-year-olds: school-related words, more complex emotions, basic reasoning words',
      7: 'Use vocabulary appropriate for early elementary: academic vocabulary, complex sentences, abstract concepts',
    };
    return guidelines[age] || guidelines[4];
  }

  const guidelines: Record<number, string> = {
    3: '만 3세 수준의 쉬운 어휘만 사용: 기본 동사(먹다, 자다, 가다, 오다), 가족 호칭(엄마, 아빠), 신체 부위, 간단한 사물',
    4: '만 4세 수준의 어휘 사용: 기본 감정 표현, 색깔, 숫자 1-10, 간단한 위치 표현(여기, 저기, 위, 아래)',
    5: '만 5세 수준의 어휘 사용: 시간 개념(오늘, 내일, 아까), 비교 표현(크다/작다), 간단한 접속 표현',
    6: '만 6세 수준의 어휘 사용: 학교 관련 어휘, 다양한 감정 표현, 기본적인 인과 표현',
    7: '초등 저학년 수준의 어휘 사용: 학습 관련 어휘, 복잡한 문장 구조, 추상적 개념 일부 포함 가능',
  };
  return guidelines[age] || guidelines[4];
}

/**
 * OpenAI GPT-5.2를 사용하여 문장들을 생성합니다.
 */
export async function generateSentencesWithAI(
  phoneme: string,
  wordCount: number,
  theme: string,
  targetCount: number,
  language: string = 'ko',
  age: number = 4
): Promise<string[]> {
  const themePrompt = getThemePrompt(theme, language);
  const ageGuideline = getAgeGuideline(age, language);

  let input: string;

  if (language === 'en') {
    const phonemePrompt = phoneme
      ? `Each sentence MUST contain a word with the '${phoneme}' sound.`
      : '';

    input = `You are a speech therapy sentence generation expert. Create sentences for ${age}-year-old children.

Generate exactly ${targetCount} English sentences with the following conditions:

Conditions:
1. Each sentence must have exactly ${wordCount} words. (Do not deviate from this)
2. ${themePrompt}
3. ${phonemePrompt}
4. ${ageGuideline}
5. Sentences should be natural and what children actually say in daily life.

Respond ONLY in this JSON format:
{"sentences": ["sentence1", "sentence2", "sentence3"]}`;
  } else {
    const phonemePrompt = phoneme
      ? `반드시 '${phoneme}' 소리(글자)가 들어간 단어를 포함해야 합니다.`
      : '';

    const examples: Record<number, string> = {
      2: '예시: "공 던져.", "책 봐.", "문 닫아.", "신발 벗어.", "밥 먹어.", "물 마셔."',
      3: '예시: "문 닫아 줘.", "불 꺼 줘.", "손 씻어 봐.", "신발 벗어 줘.", "잠깐만 멈춰."',
      4: '예시: "문 좀 닫아 줘.", "신발 빨리 신어 봐.", "이쪽으로 빨리 와."',
      5: '예시: "문 좀 닫아 줄래?", "신발 벗고 들어와 봐.", "손 깨끗이 씻어 줘."',
      6: '예시: "문 좀 닫아 줄 수 있어?", "신발 벗고 빨리 들어와 봐."',
    };

    input = `당신은 언어치료를 위한 문장 생성 전문가입니다. 만 ${age}세 아이들이 실제로 사용하는 자연스러운 문장을 만들어주세요.

다음 조건에 맞는 한국어 문장을 정확하게 ${targetCount}개 만들어주세요.

조건:
1. 정확히 ${wordCount}어절 문장이어야 합니다. (띄어쓰기로 구분, 절대 다르게 만들지 마세요)
2. ${themePrompt}
3. ${phonemePrompt}
4. ${ageGuideline}
5. 아이들이 일상에서 실제로 말하는 자연스러운 문장이어야 합니다.
6. ${examples[wordCount] || ''}

반드시 다음 JSON 형식으로만 답변해주세요:
{"sentences": ["문장1", "문장2", "문장3"]}`;
  }

  try {
    const response = await openai.responses.create({
      model: 'gpt-5.2',
      input,
      reasoning: {
        effort: 'none',
      },
    });

    const content = response.output_text;
    if (!content) {
      throw new Error('AI로부터 응답을 받지 못했습니다.');
    }

    // JSON 부분 추출 (```json 블록이 있을 수 있음)
    let jsonStr = content;
    const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      jsonStr = jsonMatch[1];
    } else {
      const objectMatch = content.match(/\{[\s\S]*\}/);
      if (objectMatch) {
        jsonStr = objectMatch[0];
      }
    }

    // JSON 파싱 시도
    const parsed = JSON.parse(jsonStr);

    // 다양한 형태의 응답 처리
    if (Array.isArray(parsed)) {
      return parsed.filter(item => typeof item === 'string');
    }

    // 객체인 경우 첫 번째 배열 값을 찾아 반환
    if (typeof parsed === 'object' && parsed !== null) {
      for (const key of Object.keys(parsed)) {
        if (Array.isArray(parsed[key])) {
          return parsed[key].filter((item: unknown) => typeof item === 'string');
        }
      }
    }

    throw new Error('예상하지 못한 응답 형식입니다.');
  } catch (error) {
    console.error('OpenAI API Error:', error);
    throw error;
  }
}

/**
 * 필터링 로직이 포함된 문장 생성 함수.
 * 필요한 만큼 조건에 맞는 문장을 얻을 때까지 반복합니다.
 */
export async function generateFilteredSentences(
  phoneme: string,
  wordCount: number,
  theme: string,
  targetCount: number,
  language: string = 'ko',
  age: number = 4,
  maxAttempts: number = 3
): Promise<string[]> {
  const uniqueSentences = new Set<string>();
  let attempts = 0;

  while (uniqueSentences.size < targetCount && attempts < maxAttempts) {
    const batchSize = Math.max(targetCount - uniqueSentences.size + 5, 10);
    const sentences = await generateSentencesWithAI(phoneme, wordCount, theme, batchSize, language, age);

    const { filterSentences } = await import('./utils');
    const newFiltered = filterSentences(sentences, wordCount, phoneme, language);

    for (const sentence of newFiltered) {
      uniqueSentences.add(sentence);
    }
    attempts++;
  }

  return Array.from(uniqueSentences).slice(0, targetCount);
}
