// Language and settings types
export type LanguageV2 = 'ko' | 'en';
export type DiagnosisType = 'SSD' | 'ASD' | 'LD';
export type TherapyApproach = 'minimal_pairs' | 'maximal_oppositions' | 'complexity' | 'core_vocabulary';
export type CommunicativeFunction = 'request' | 'reject' | 'help' | 'choice' | 'attention' | 'question';
export type PhonemePosition = 'onset' | 'nucleus' | 'coda' | 'any';

// Difficulty level for therapy items
export type DifficultyLevel = 'easy' | 'medium' | 'hard';

// Phonological rules mode for SSD therapy
export type PhonologicalRulesMode = 'avoid' | 'allow' | 'train';

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
  difficulty?: DifficultyLevel;
  tokens?: string[];  // Tokenized form of the sentence
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
  coreWords?: string[];  // For core_vocabulary approach
  phonologicalRulesMode?: PhonologicalRulesMode;
}

// Session color options
export type SessionColor = 'purple' | 'pink' | 'blue' | 'green' | 'orange' | 'red';

// Tokenized sentence for contrast sets
export interface TokenizedSentence {
  text: string;
  tokens: string[];
}

// Contrast set for minimal_pairs/maximal_oppositions approaches
export interface ContrastSet {
  targetWord: string;
  contrastWord: string;
  targetSentence: TokenizedSentence;
  contrastSentence: TokenizedSentence;
}

// Script fading result for ASD script approach
export interface ScriptFadingResult {
  fullScript: string;
  fadeSteps: string[];
}

// Therapy session for IndexedDB storage
export interface TherapySession {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
  settings: GameSettingsV2;
  items: TherapyItemV2[];
  metadata: {
    patientName?: string;
    notes?: string;
    color?: SessionColor;
  };
}
