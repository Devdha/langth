// 문장 하나를 나타내는 타입
export interface TherapyItem {
  id: string;
  text: string;      // 실제 문장 (예: "다람쥐가 도토리를 먹어요")
  targetPhoneme: string; // 타겟 음소 (예: "ㄹ")
  wordCount: number; // 어절 수 (예: 3)
  theme?: string;    // 주제 (선택)
}

// 사용자 설정 타입
export interface GameSettings {
  phoneme: string;   // 'ㅅ', 'ㄹ', '' (없으면 무관)
  level: 2 | 3 | 4 | 5 | 6;  // 어절 수
  theme: string;     // 'daily', 'food', 'animal', 'family', '' (없으면 무관)
  count: number;     // 생성할 문장 수
  language: 'ko' | 'en';  // 언어 선택
  age: 3 | 4 | 5 | 6 | 7;  // 연령 (만 나이)
}

// API 요청/응답 타입
export interface GenerateRequest {
  settings: GameSettings;
}

export interface GenerateResponse {
  success: boolean;
  items: TherapyItem[];
  error?: string;
}

// 게임 모드 타입
export type GameMode = 'list' | 'roulette' | 'cards' | 'ladder';

// 룰렛 섹션 타입
export interface RouletteSection {
  label: string;
  value: TherapyItem;
  color: string;
}
