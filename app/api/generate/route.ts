import { NextRequest, NextResponse } from 'next/server';
import { generateFilteredSentences } from '@/lib/openai';
import { generateId } from '@/lib/utils';
import type { GenerateRequest, GenerateResponse, TherapyItem } from '@/types';

export async function POST(request: NextRequest) {
  try {
    const body: GenerateRequest = await request.json();
    const { settings } = body;

    if (!settings) {
      return NextResponse.json(
        { success: false, error: '설정이 필요합니다.' },
        { status: 400 }
      );
    }

    const { phoneme, level, theme, count, language, age } = settings;

    const sentences = await generateFilteredSentences(
      phoneme,
      level,
      theme,
      count,
      language || 'ko',
      age || 4
    );

    const items: TherapyItem[] = sentences.map((text) => ({
      id: generateId(),
      text,
      targetPhoneme: phoneme,
      wordCount: level,
      theme: theme || undefined,
    }));

    const response: GenerateResponse = {
      success: true,
      items,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: '문장 생성 중 오류가 발생했습니다.',
        items: [],
      },
      { status: 500 }
    );
  }
}
