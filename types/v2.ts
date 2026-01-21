// Language and settings types
export type LanguageV2 = 'ko' | 'en';
export type DiagnosisType = 'SSD' | 'ASD' | 'LD';
export type TherapyApproach = 'minimal_pairs' | 'maximal_oppositions' | 'complexity' | 'core_vocabulary';
export type CommunicativeFunction = 'request' | 'reject' | 'help' | 'choice' | 'attention' | 'question';
export type PhonemePosition = 'onset' | 'nucleus' | 'coda' | 'any';

// Target configuration
export interface TargetConfigV2 {
  phoneme: string;
  position: PhonemePosition;
  minOccurrences: number;
}

// Matched word for highlighting
export interface MatchedWord {
  word: string;
  startIndex: number;
  endIndex: number;
  positions: PhonemePosition[];
}

// V2 therapy item with enhanced metadata
export interface TherapyItemV2 {
  id: string;
  text: string;
  target: TargetConfigV2;
  matchedWords: MatchedWord[];
  wordCount: number;
  score: number;
  diagnosis: DiagnosisType;
  approach: TherapyApproach;
  theme?: string;
  function?: CommunicativeFunction;
}

// V2 generation request
export interface GenerateRequestV2 {
  language: LanguageV2;
  age: 3 | 4 | 5 | 6 | 7;
  count: number;
  target: TargetConfigV2;
  sentenceLength: number;
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  theme?: string;
  communicativeFunction?: CommunicativeFunction;
}

// V2 generation response
export interface GenerateResponseV2 {
  success: true;
  data: {
    items: TherapyItemV2[];
    meta: {
      requestedCount: number;
      generatedCount: number;
      averageScore: number;
      processingTimeMs: number;
    };
  };
}

export interface ErrorResponseV2 {
  success: false;
  error: {
    code: string;
    message: string;
    details?: string;
  };
}

// V2 game settings (for localStorage)
export interface GameSettingsV2 {
  language: LanguageV2;
  age: 3 | 4 | 5 | 6 | 7;
  count: number;
  target: TargetConfigV2;
  sentenceLength: number;
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  theme: string;
  communicativeFunction: CommunicativeFunction | null;
}
