# Phase 3: V2 프론트엔드 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** v2 백엔드 API와 연동하는 새로운 `/v2` 페이지 구현 (진단군 프리셋, 음소 위치 선택, 하이라이트 표시)

**Architecture:** Next.js App Router 기반, v1과 동일한 디자인 시스템 활용, Python 백엔드(`localhost:8000`)와 API 통신

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS v4, Framer Motion, Lucide Icons

---

## Task 3.1: V2 타입 정의 및 페이지 기본 구조

**Files:**
- Create: `types/v2.ts`
- Create: `app/v2/page.tsx`

### Step 1: V2 타입 정의 작성

`types/v2.ts`:
```typescript
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
  score: float;
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
```

### Step 2: V2 페이지 기본 구조 작성

`app/v2/page.tsx`:
```typescript
"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import { TherapyItemV2, GameSettingsV2 } from "@/types/v2";

const STORAGE_KEY_V2 = 'talk-talk-vending-v2-items';
const SETTINGS_KEY_V2 = 'talk-talk-vending-v2-settings';
const LOADING_TIMEOUT = 60000; // 60초 (v2는 더 오래 걸릴 수 있음)

const DEFAULT_SETTINGS: GameSettingsV2 = {
  language: 'ko',
  age: 4,
  count: 10,
  target: {
    phoneme: 'ㄹ',
    position: 'onset',
    minOccurrences: 1,
  },
  sentenceLength: 3,
  diagnosis: 'SSD',
  therapyApproach: 'minimal_pairs',
  theme: '',
  communicativeFunction: null,
};

export default function V2Page() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [items, setItems] = useState<TherapyItemV2[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [settings, setSettings] = useState<GameSettingsV2>(DEFAULT_SETTINGS);
  const abortControllerRef = useRef<AbortController | null>(null);

  // localStorage에서 데이터 로드
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedItems = localStorage.getItem(STORAGE_KEY_V2);
      const savedSettings = localStorage.getItem(SETTINGS_KEY_V2);

      if (savedItems) {
        try {
          setItems(JSON.parse(savedItems));
        } catch (e) {
          console.error('Failed to parse saved v2 items', e);
        }
      }

      if (savedSettings) {
        try {
          setSettings(JSON.parse(savedSettings));
        } catch (e) {
          console.error('Failed to parse saved v2 settings', e);
        }
      }

      setIsInitialized(true);
    }
  }, []);

  // items 변경 시 localStorage에 저장
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(items));
    }
  }, [items, isInitialized]);

  // settings 변경 시 localStorage에 저장
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(SETTINGS_KEY_V2, JSON.stringify(settings));
    }
  }, [settings, isInitialized]);

  const handleReset = () => {
    if (confirm('모든 문장을 삭제하시겠습니까?')) {
      setItems([]);
      setError(null);
    }
  };

  // TODO: handleGenerate - Task 3.3에서 useGenerateV2 훅으로 구현

  return (
    <main className="min-h-screen bg-background text-foreground pb-20">
      <Header
        currentMode="list"
        onModeChange={() => {}}
        onNewGame={() => setIsSettingsOpen(true)}
        isV2={true}
      />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* V2 배지 */}
        <div className="flex items-center gap-2 mb-6">
          <span className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-bold rounded-full">
            V2 Beta
          </span>
          <span className="text-gray-500 text-sm">
            임상적으로 검증된 음소 위치 기반 문장 생성
          </span>
        </div>

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loader"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-xl font-bold text-gray-500 animate-pulse mb-4">
                4단계 파이프라인으로 문장을 생성 중...
              </p>
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="text-6xl mb-4">😢</div>
              <p className="text-xl font-bold text-red-500 mb-4">{error}</p>
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="px-6 py-3 bg-purple-500 text-white rounded-xl font-bold hover:bg-purple-600 transition-colors"
              >
                다시 시도하기
              </button>
            </motion.div>
          ) : items.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-xl font-bold text-gray-500 mb-4">
                V2 엔진으로 문장을 생성해보세요!
              </p>
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-bold hover:opacity-90 transition-opacity"
              >
                시작하기
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="flex justify-between items-center mb-6 px-2">
                <h2 className="text-2xl font-bold text-gray-700 flex items-center gap-2">
                  <span className="text-3xl">📋</span> 연습 목록
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 font-bold bg-white px-3 py-1 rounded-lg border border-gray-100 shadow-sm">
                    총 {items.length}개
                  </span>
                  <button
                    onClick={handleReset}
                    className="px-3 py-1 text-sm font-bold text-red-500 bg-red-50 rounded-lg border border-red-100 hover:bg-red-100 transition-colors"
                  >
                    초기화
                  </button>
                </div>
              </div>
              {/* TODO: SentenceListV2 컴포넌트 - Task 3.4에서 구현 */}
              <div className="text-center text-gray-500">
                SentenceListV2 컴포넌트 구현 예정
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* TODO: SettingsPanelV2 - Task 3.2에서 구현 */}
    </main>
  );
}
```

### Step 3: 테스트

Run: `npm run dev` 후 브라우저에서 `http://localhost:3000/v2` 접속
Expected: V2 페이지 기본 레이아웃 표시, "시작하기" 버튼 표시

### Step 4: 커밋

```bash
git add types/v2.ts app/v2/page.tsx
git commit -m "feat(frontend): add v2 types and page skeleton"
```

---

## Task 3.2: SettingsPanelV2 컴포넌트

**Files:**
- Create: `components/v2/SettingsPanelV2.tsx`
- Create: `components/v2/DiagnosisSelector.tsx`
- Create: `components/v2/PhonemeSelector.tsx`
- Modify: `app/v2/page.tsx`

### Step 1: 진단군 선택 컴포넌트 작성

`components/v2/DiagnosisSelector.tsx`:
```typescript
"use client";

import { DiagnosisType, TherapyApproach } from "@/types/v2";

interface DiagnosisSelectorProps {
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  onDiagnosisChange: (diagnosis: DiagnosisType) => void;
  onApproachChange: (approach: TherapyApproach) => void;
}

const DIAGNOSES = [
  {
    id: 'SSD' as const,
    label: '말소리장애',
    icon: '🗣️',
    desc: 'Speech Sound Disorder',
    approaches: [
      { id: 'minimal_pairs' as const, label: '최소대립쌍', desc: '비슷한 소리 구별' },
      { id: 'maximal_oppositions' as const, label: '최대대립', desc: '대조적 소리 연습' },
      { id: 'complexity' as const, label: '복잡성 접근', desc: '어려운 소리부터' },
    ]
  },
  {
    id: 'ASD' as const,
    label: '자폐스펙트럼',
    icon: '🧩',
    desc: 'Autism Spectrum Disorder',
    approaches: [
      { id: 'core_vocabulary' as const, label: '핵심어휘', desc: '자주 쓰는 단어 중심' },
    ]
  },
  {
    id: 'LD' as const,
    label: '언어발달지연',
    icon: '📚',
    desc: 'Language Delay',
    approaches: [
      { id: 'core_vocabulary' as const, label: '핵심어휘', desc: '기초 어휘 확장' },
    ]
  },
];

export default function DiagnosisSelector({
  diagnosis,
  therapyApproach,
  onDiagnosisChange,
  onApproachChange,
}: DiagnosisSelectorProps) {
  const selectedDiagnosis = DIAGNOSES.find(d => d.id === diagnosis)!;

  // 진단군 변경 시 첫 번째 접근법으로 자동 설정
  const handleDiagnosisChange = (newDiagnosis: DiagnosisType) => {
    const newDiag = DIAGNOSES.find(d => d.id === newDiagnosis)!;
    onDiagnosisChange(newDiagnosis);
    onApproachChange(newDiag.approaches[0].id);
  };

  return (
    <div className="space-y-6">
      {/* 진단군 선택 */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">진단군</h4>
        <div className="grid grid-cols-3 gap-3">
          {DIAGNOSES.map((d) => (
            <button
              key={d.id}
              onClick={() => handleDiagnosisChange(d.id)}
              className={`p-4 rounded-2xl border-2 transition-all text-center ${
                diagnosis === d.id
                  ? 'border-purple-500 bg-purple-50 ring-4 ring-purple-500/20'
                  : 'border-gray-100 hover:border-gray-200 bg-white'
              }`}
            >
              <div className="text-3xl mb-2">{d.icon}</div>
              <div className="font-bold text-gray-700 text-sm">{d.label}</div>
              <div className="text-xs text-gray-400 mt-1">{d.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 치료 접근법 선택 */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">치료 접근법</h4>
        <div className="flex flex-wrap gap-2">
          {selectedDiagnosis.approaches.map((a) => (
            <button
              key={a.id}
              onClick={() => onApproachChange(a.id)}
              className={`px-4 py-2 rounded-xl font-medium transition-all ${
                therapyApproach === a.id
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span>{a.label}</span>
              <span className={`text-xs ml-1 ${therapyApproach === a.id ? 'text-purple-200' : 'text-gray-400'}`}>
                ({a.desc})
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Step 2: 음소 선택 컴포넌트 작성 (위치 선택 포함)

`components/v2/PhonemeSelector.tsx`:
```typescript
"use client";

import { TargetConfigV2, LanguageV2, PhonemePosition } from "@/types/v2";

interface PhonemeSelectorProps {
  target: TargetConfigV2;
  language: LanguageV2;
  onChange: (target: TargetConfigV2) => void;
}

const KOREAN_PHONEMES = {
  onset: ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'],
  nucleus: ['ㅏ', 'ㅓ', 'ㅗ', 'ㅜ', 'ㅡ', 'ㅣ', 'ㅐ', 'ㅔ', 'ㅚ', 'ㅟ'],
  coda: ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅇ'],
};

const ENGLISH_PHONEMES = {
  onset: ['R', 'L', 'S', 'TH', 'SH', 'CH', 'K', 'G', 'F', 'V'],
  coda: ['R', 'L', 'S', 'Z', 'TH', 'NG', 'K', 'T'],
};

const POSITIONS: { id: PhonemePosition; label: string; desc: string }[] = [
  { id: 'onset', label: '초성', desc: '어두/음절 처음' },
  { id: 'coda', label: '종성', desc: '어말/음절 끝' },
  { id: 'any', label: '전체', desc: '위치 무관' },
];

const OCCURRENCES = [1, 2, 3];

export default function PhonemeSelector({ target, language, onChange }: PhonemeSelectorProps) {
  const phonemes = language === 'ko'
    ? (target.position === 'nucleus' ? KOREAN_PHONEMES.nucleus :
       target.position === 'coda' ? KOREAN_PHONEMES.coda : KOREAN_PHONEMES.onset)
    : (target.position === 'coda' ? ENGLISH_PHONEMES.coda : ENGLISH_PHONEMES.onset);

  // 한국어에서 ㅇ은 종성에서만 유효 (비음 [ŋ])
  const isValidPhoneme = (phoneme: string) => {
    if (language === 'ko' && phoneme === 'ㅇ') {
      return target.position === 'coda' || target.position === 'any';
    }
    return true;
  };

  return (
    <div className="space-y-6">
      {/* 위치 선택 */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">음소 위치</h4>
        <div className="flex gap-3">
          {POSITIONS.map((p) => (
            <button
              key={p.id}
              onClick={() => onChange({ ...target, position: p.id })}
              className={`flex-1 px-4 py-3 rounded-xl font-bold transition-all ${
                target.position === p.id
                  ? 'bg-secondary text-white shadow-lg shadow-secondary/30'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              <div>{p.label}</div>
              <div className={`text-xs ${target.position === p.id ? 'text-secondary-foreground/70' : 'text-gray-400'}`}>
                {p.desc}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 음소 선택 */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">목표 음소</h4>
        <div className="grid grid-cols-5 sm:grid-cols-7 gap-2">
          {phonemes.map((p) => {
            const valid = isValidPhoneme(p);
            return (
              <button
                key={p}
                onClick={() => valid && onChange({ ...target, phoneme: p })}
                disabled={!valid}
                className={`aspect-square rounded-xl text-lg font-bold transition-all transform hover:scale-105 active:scale-95 ${
                  target.phoneme === p
                    ? 'bg-secondary text-white shadow-lg shadow-secondary/30 ring-4 ring-secondary/20'
                    : valid
                      ? 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      : 'bg-gray-50 text-gray-300 cursor-not-allowed'
                }`}
              >
                {p}
              </button>
            );
          })}
        </div>
        {language === 'ko' && target.position === 'onset' && (
          <p className="text-xs text-gray-400 mt-2">
            * 'ㅇ'은 초성에서 무음이므로 종성(비음 [ŋ])에서만 선택 가능합니다
          </p>
        )}
      </div>

      {/* 최소 출현 횟수 */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-3">최소 출현 횟수</h4>
        <div className="flex gap-3">
          {OCCURRENCES.map((n) => (
            <button
              key={n}
              onClick={() => onChange({ ...target, minOccurrences: n })}
              className={`w-12 h-12 rounded-full text-lg font-bold transition-all ${
                target.minOccurrences === n
                  ? 'bg-accent text-white shadow-lg shadow-accent/30'
                  : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2">
          문장 내 목표 음소가 최소 {target.minOccurrences}회 이상 포함됩니다
        </p>
      </div>
    </div>
  );
}
```

### Step 3: SettingsPanelV2 메인 컴포넌트 작성

`components/v2/SettingsPanelV2.tsx`:
```typescript
"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles } from "lucide-react";
import { GameSettingsV2, CommunicativeFunction, LanguageV2 } from "@/types/v2";
import DiagnosisSelector from "./DiagnosisSelector";
import PhonemeSelector from "./PhonemeSelector";

interface SettingsPanelV2Props {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (settings: GameSettingsV2) => void;
  initialSettings: GameSettingsV2;
}

const THEMES = [
  { id: '', label: '없음', icon: '✨' },
  { id: 'daily', label: '일상', icon: '🏠' },
  { id: 'food', label: '음식', icon: '🍽️' },
  { id: 'animal', label: '동물', icon: '🐶' },
  { id: 'family', label: '가족', icon: '👨‍👩‍👧' },
];

const AGES = [
  { id: 3, label: '만 3세' },
  { id: 4, label: '만 4세' },
  { id: 5, label: '만 5세' },
  { id: 6, label: '만 6세' },
  { id: 7, label: '만 7세' },
];

const LANGUAGES = [
  { id: 'ko' as const, label: '한국어', icon: '🇰🇷' },
  { id: 'en' as const, label: 'English', icon: '🇺🇸' },
];

const COUNTS = [5, 10, 15, 20];
const SENTENCE_LENGTHS = [2, 3, 4, 5, 6];

const COMMUNICATIVE_FUNCTIONS: { id: CommunicativeFunction | null; label: string; icon: string }[] = [
  { id: null, label: '없음', icon: '✨' },
  { id: 'request', label: '요청하기', icon: '🙏' },
  { id: 'reject', label: '거부하기', icon: '🙅' },
  { id: 'help', label: '도움 요청', icon: '🆘' },
  { id: 'choice', label: '선택하기', icon: '🤔' },
  { id: 'attention', label: '관심 끌기', icon: '👀' },
  { id: 'question', label: '질문하기', icon: '❓' },
];

export default function SettingsPanelV2({ isOpen, onClose, onGenerate, initialSettings }: SettingsPanelV2Props) {
  const [settings, setSettings] = useState<GameSettingsV2>(initialSettings);

  useEffect(() => {
    if (isOpen) {
      setSettings(initialSettings);
    }
  }, [isOpen, initialSettings]);

  const handleGenerate = () => {
    onGenerate(settings);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden border-4 border-purple-500/20"
          >
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-6 flex justify-between items-center border-b-2 border-purple-500/10">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <span className="text-3xl">⚙️</span> V2 설정
                <span className="px-2 py-0.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold rounded-full">
                  Beta
                </span>
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-black/5 rounded-full transition-colors"
              >
                <X size={24} className="text-gray-500" />
              </button>
            </div>

            <div className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">

              {/* Section 1: 진단군 & 치료접근법 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center text-sm">1</span>
                  진단군 및 접근법
                </h3>
                <DiagnosisSelector
                  diagnosis={settings.diagnosis}
                  therapyApproach={settings.therapyApproach}
                  onDiagnosisChange={(d) => setSettings({ ...settings, diagnosis: d })}
                  onApproachChange={(a) => setSettings({ ...settings, therapyApproach: a })}
                />
              </section>

              {/* Section 2: 목표 음소 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-secondary text-white flex items-center justify-center text-sm">2</span>
                  목표 음소
                </h3>
                <PhonemeSelector
                  target={settings.target}
                  language={settings.language}
                  onChange={(t) => setSettings({ ...settings, target: t })}
                />
              </section>

              {/* Section 3: 문장 길이 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-sm">3</span>
                  문장 길이 (어절)
                </h3>
                <div className="flex gap-4 justify-center">
                  {SENTENCE_LENGTHS.map((n) => (
                    <button
                      key={n}
                      onClick={() => setSettings({ ...settings, sentenceLength: n })}
                      className={`w-14 h-14 rounded-full text-xl font-bold transition-all transform hover:scale-110 active:scale-90 ${
                        settings.sentenceLength === n
                          ? 'bg-accent text-white shadow-lg shadow-accent/30 ring-4 ring-accent/20'
                          : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </section>

              {/* Section 4: 주제 & 의사소통 기능 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-info text-white flex items-center justify-center text-sm">4</span>
                  주제 및 의사소통 기능 (선택)
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-2">주제</h4>
                    <div className="flex flex-wrap gap-2">
                      {THEMES.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setSettings({ ...settings, theme: t.id })}
                          className={`px-4 py-2 rounded-xl font-medium transition-all ${
                            settings.theme === t.id
                              ? 'bg-info text-white shadow-lg shadow-info/30'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <span className="mr-1">{t.icon}</span>
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-2">의사소통 기능</h4>
                    <div className="flex flex-wrap gap-2">
                      {COMMUNICATIVE_FUNCTIONS.map((f) => (
                        <button
                          key={f.id ?? 'none'}
                          onClick={() => setSettings({ ...settings, communicativeFunction: f.id })}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                            settings.communicativeFunction === f.id
                              ? 'bg-pink-500 text-white shadow-lg shadow-pink-500/30'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <span className="mr-1">{f.icon}</span>
                          {f.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 5: 연령 & 언어 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-teal-500 text-white flex items-center justify-center text-sm">5</span>
                  연령 및 언어
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-2">연령</h4>
                    <div className="flex flex-wrap gap-2">
                      {AGES.map((a) => (
                        <button
                          key={a.id}
                          onClick={() => setSettings({ ...settings, age: a.id as 3|4|5|6|7 })}
                          className={`px-3 py-2 rounded-xl font-bold transition-all ${
                            settings.age === a.id
                              ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/30'
                              : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-2">언어</h4>
                    <div className="flex gap-2">
                      {LANGUAGES.map((l) => (
                        <button
                          key={l.id}
                          onClick={() => setSettings({ ...settings, language: l.id })}
                          className={`px-4 py-2 rounded-xl font-bold transition-all flex items-center gap-1 ${
                            settings.language === l.id
                              ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                              : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          <span>{l.icon}</span>
                          {l.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 6: 개수 */}
              <section>
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-pink-500 text-white flex items-center justify-center text-sm">6</span>
                  생성 개수
                </h3>
                <div className="flex gap-4 justify-center">
                  {COUNTS.map((n) => (
                    <button
                      key={n}
                      onClick={() => setSettings({ ...settings, count: n })}
                      className={`w-14 h-14 rounded-full text-lg font-bold transition-all transform hover:scale-110 active:scale-90 ${
                        settings.count === n
                          ? 'bg-pink-500 text-white shadow-lg shadow-pink-500/30 ring-4 ring-pink-500/20'
                          : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </section>

            </div>

            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-6 py-3 rounded-xl font-bold text-gray-500 hover:bg-gray-100 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleGenerate}
                className="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg hover:shadow-xl hover:opacity-90 transition-all transform hover:-translate-y-1 active:translate-y-0 flex items-center gap-2"
              >
                <Sparkles className="fill-white" size={20} />
                문장 생성
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Step 4: V2 페이지에 SettingsPanelV2 연결

`app/v2/page.tsx` 수정:
```typescript
// 상단 import 추가
import SettingsPanelV2 from "@/components/v2/SettingsPanelV2";

// return문 마지막에 SettingsPanelV2 추가
<SettingsPanelV2
  isOpen={isSettingsOpen}
  onClose={() => setIsSettingsOpen(false)}
  onGenerate={(newSettings) => {
    setSettings(newSettings);
    // TODO: Task 3.3에서 API 호출 구현
  }}
  initialSettings={settings}
/>
```

### Step 5: 테스트

Run: `npm run dev`
Expected: /v2 페이지에서 "시작하기" 버튼 클릭 시 SettingsPanelV2 모달 표시

### Step 6: 커밋

```bash
git add components/v2/
git add app/v2/page.tsx
git commit -m "feat(frontend): add SettingsPanelV2 with diagnosis and phoneme selectors"
```

---

## Task 3.3: useGenerateV2 훅 (API 연동)

**Files:**
- Create: `hooks/useGenerateV2.ts`
- Modify: `app/v2/page.tsx`

### Step 1: useGenerateV2 훅 작성

`hooks/useGenerateV2.ts`:
```typescript
"use client";

import { useState, useRef, useCallback } from "react";
import { GameSettingsV2, TherapyItemV2, GenerateResponseV2, ErrorResponseV2, GenerateRequestV2 } from "@/types/v2";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const LOADING_TIMEOUT = 60000; // 60초

interface UseGenerateV2Result {
  generate: (settings: GameSettingsV2) => Promise<void>;
  cancel: () => void;
  loading: boolean;
  error: string | null;
  items: TherapyItemV2[];
  warning: string | null;
  meta: {
    requestedCount: number;
    generatedCount: number;
    averageScore: number;
    processingTimeMs: number;
  } | null;
}

export function useGenerateV2(
  onSuccess?: (items: TherapyItemV2[]) => void,
): UseGenerateV2Result {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<TherapyItemV2[]>([]);
  const [warning, setWarning] = useState<string | null>(null);
  const [meta, setMeta] = useState<UseGenerateV2Result['meta']>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const generate = useCallback(async (settings: GameSettingsV2) => {
    setLoading(true);
    setError(null);
    setWarning(null);

    abortControllerRef.current = new AbortController();
    const timeoutId = setTimeout(() => {
      abortControllerRef.current?.abort();
    }, LOADING_TIMEOUT);

    try {
      const requestBody: GenerateRequestV2 = {
        language: settings.language,
        age: settings.age,
        count: settings.count,
        target: settings.target,
        sentenceLength: settings.sentenceLength,
        diagnosis: settings.diagnosis,
        therapyApproach: settings.therapyApproach,
        theme: settings.theme || undefined,
        communicativeFunction: settings.communicativeFunction || undefined,
      };

      const res = await fetch(`${API_BASE_URL}/api/v2/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });

      clearTimeout(timeoutId);

      const data = await res.json();

      if (res.ok && data.success) {
        const response = data as GenerateResponseV2;
        setItems(response.data.items);
        setMeta(response.data.meta);

        if (response.data.meta.generatedCount < response.data.meta.requestedCount) {
          setWarning(
            `요청한 ${response.data.meta.requestedCount}개 중 ` +
            `${response.data.meta.generatedCount}개만 생성되었습니다.`
          );
        }

        onSuccess?.(response.data.items);
      } else {
        const errorResponse = data as ErrorResponseV2;
        setError(errorResponse.error?.message || '문장 생성에 실패했습니다.');
      }
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof Error && err.name === 'AbortError') {
        setError('요청 시간이 초과되었습니다. 다시 시도해주세요.');
      } else {
        console.error("Failed to generate v2", err);
        setError('서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인해주세요.');
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [onSuccess]);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  return { generate, cancel, loading, error, items, warning, meta };
}
```

### Step 2: V2 페이지에 훅 연결

`app/v2/page.tsx` 수정:
```typescript
// import 추가
import { useGenerateV2 } from "@/hooks/useGenerateV2";

// useGenerateV2 훅 사용
const { generate, cancel, loading, error, items: generatedItems, warning, meta } = useGenerateV2(
  (newItems) => setItems(newItems)
);

// handleGenerate 함수 교체
const handleGenerate = async (newSettings: GameSettingsV2) => {
  setSettings(newSettings);
  await generate(newSettings);
};

// SettingsPanelV2 onGenerate prop 수정
onGenerate={handleGenerate}
```

### Step 3: 로딩 UI에 취소 버튼 추가

로딩 상태 UI 수정:
```typescript
{loading ? (
  <motion.div ...>
    ...
    <button
      onClick={cancel}
      className="px-4 py-2 text-sm font-bold text-gray-500 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
    >
      취소
    </button>
  </motion.div>
)
```

### Step 4: 테스트

1. Python 백엔드 실행: `cd backend && python -m uvicorn app.main:app --reload`
2. 프론트엔드 실행: `npm run dev`
3. /v2 접속 → 설정 → 문장 생성

Expected: 백엔드에서 문장 생성 응답 받음

### Step 5: 커밋

```bash
git add hooks/useGenerateV2.ts app/v2/page.tsx
git commit -m "feat(frontend): add useGenerateV2 hook for API integration"
```

---

## Task 3.4: SentenceListV2 (하이라이트)

**Files:**
- Create: `components/v2/HighlightedText.tsx`
- Create: `components/v2/SentenceListV2.tsx`
- Create: `components/v2/SentenceCardV2.tsx`
- Modify: `app/v2/page.tsx`

### Step 1: HighlightedText 컴포넌트 작성

`components/v2/HighlightedText.tsx`:
```typescript
"use client";

import { MatchedWord } from "@/types/v2";

interface HighlightedTextProps {
  text: string;
  matchedWords: MatchedWord[];
  highlightClass?: string;
}

export default function HighlightedText({
  text,
  matchedWords,
  highlightClass = "bg-yellow-200 text-yellow-900 px-0.5 rounded font-bold"
}: HighlightedTextProps) {
  if (!matchedWords || matchedWords.length === 0) {
    return <span>{text}</span>;
  }

  // 매칭된 단어들을 startIndex로 정렬
  const sortedMatches = [...matchedWords].sort((a, b) => a.startIndex - b.startIndex);

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  sortedMatches.forEach((match, idx) => {
    // 매칭 전 텍스트
    if (match.startIndex > lastIndex) {
      parts.push(
        <span key={`text-${idx}`}>
          {text.slice(lastIndex, match.startIndex)}
        </span>
      );
    }

    // 하이라이트된 텍스트
    parts.push(
      <mark key={`match-${idx}`} className={highlightClass}>
        {text.slice(match.startIndex, match.endIndex)}
      </mark>
    );

    lastIndex = match.endIndex;
  });

  // 마지막 매칭 이후 텍스트
  if (lastIndex < text.length) {
    parts.push(
      <span key="text-last">
        {text.slice(lastIndex)}
      </span>
    );
  }

  return <>{parts}</>;
}
```

### Step 2: SentenceCardV2 컴포넌트 작성

`components/v2/SentenceCardV2.tsx`:
```typescript
"use client";

import { motion } from "framer-motion";
import { Trash2, Edit2, Volume2 } from "lucide-react";
import { TherapyItemV2 } from "@/types/v2";
import HighlightedText from "./HighlightedText";

interface SentenceCardV2Props {
  item: TherapyItemV2;
  index: number;
  onDelete: (id: string) => void;
  onEdit: (item: TherapyItemV2) => void;
  onPlay: (item: TherapyItemV2) => void;
}

const DIAGNOSIS_BADGES = {
  SSD: { label: '말소리', color: 'bg-purple-100 text-purple-700' },
  ASD: { label: '자폐스펙트럼', color: 'bg-blue-100 text-blue-700' },
  LD: { label: '언어발달', color: 'bg-green-100 text-green-700' },
};

export default function SentenceCardV2({ item, index, onDelete, onEdit, onPlay }: SentenceCardV2Props) {
  const badge = DIAGNOSIS_BADGES[item.diagnosis];
  const scorePercent = Math.round(item.score * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow group"
    >
      {/* 상단 메타 정보 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
            {badge.label}
          </span>
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            {item.target.phoneme} · {item.target.position === 'onset' ? '초성' : item.target.position === 'coda' ? '종성' : '전체'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
          <span className="text-xs text-gray-400 w-8">{scorePercent}%</span>
        </div>
      </div>

      {/* 문장 텍스트 (하이라이트) */}
      <p className="text-xl font-bold text-gray-800 mb-4 leading-relaxed">
        <HighlightedText text={item.text} matchedWords={item.matchedWords} />
      </p>

      {/* 하단 정보 및 액션 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{item.wordCount}어절</span>
          {item.function && (
            <>
              <span>·</span>
              <span>{item.function}</span>
            </>
          )}
          {item.matchedWords.length > 0 && (
            <>
              <span>·</span>
              <span className="text-yellow-600">
                {item.matchedWords.length}개 매칭
              </span>
            </>
          )}
        </div>

        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onPlay(item)}
            className="p-2 rounded-lg hover:bg-blue-50 text-blue-500 transition-colors"
            title="듣기"
          >
            <Volume2 size={18} />
          </button>
          <button
            onClick={() => onEdit(item)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
            title="수정"
          >
            <Edit2 size={18} />
          </button>
          <button
            onClick={() => onDelete(item.id)}
            className="p-2 rounded-lg hover:bg-red-50 text-red-500 transition-colors"
            title="삭제"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
```

### Step 3: SentenceListV2 컴포넌트 작성

`components/v2/SentenceListV2.tsx`:
```typescript
"use client";

import { AnimatePresence } from "framer-motion";
import { TherapyItemV2 } from "@/types/v2";
import SentenceCardV2 from "./SentenceCardV2";

interface SentenceListV2Props {
  items: TherapyItemV2[];
  onDelete: (id: string) => void;
  onEdit: (item: TherapyItemV2) => void;
  onPlay: (item: TherapyItemV2) => void;
}

export default function SentenceListV2({ items, onDelete, onEdit, onPlay }: SentenceListV2Props) {
  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">📝</div>
        <p className="text-gray-400 font-medium">
          아직 생성된 문장이 없습니다
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <SentenceCardV2
            key={item.id}
            item={item}
            index={index}
            onDelete={onDelete}
            onEdit={onEdit}
            onPlay={onPlay}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
```

### Step 4: V2 페이지에 SentenceListV2 연결

`app/v2/page.tsx` 수정:
```typescript
// import 추가
import SentenceListV2 from "@/components/v2/SentenceListV2";

// 핸들러 함수 추가
const handleDelete = (id: string) => {
  setItems(items.filter(item => item.id !== id));
};

const handleEdit = (item: TherapyItemV2) => {
  // TODO: EditModal 연결
  console.log('Edit:', item);
};

const handlePlay = (item: TherapyItemV2) => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(item.text);
    utterance.lang = settings.language === 'en' ? 'en-US' : 'ko-KR';
    window.speechSynthesis.speak(utterance);
  }
};

// SentenceListV2 교체
<SentenceListV2
  items={items}
  onDelete={handleDelete}
  onEdit={handleEdit}
  onPlay={handlePlay}
/>
```

### Step 5: 테스트

Expected: 문장 카드에 하이라이트된 텍스트, 점수 바, 진단군 배지 표시

### Step 6: 커밋

```bash
git add components/v2/HighlightedText.tsx components/v2/SentenceCardV2.tsx components/v2/SentenceListV2.tsx
git add app/v2/page.tsx
git commit -m "feat(frontend): add SentenceListV2 with phoneme highlighting"
```

---

## Task 3.5: 버전 전환 UI

**Files:**
- Modify: `components/Header.tsx`
- Modify: `app/page.tsx`

### Step 1: Header에 isV2 prop 추가

`components/Header.tsx` 수정:
```typescript
interface HeaderProps {
  currentMode: GameMode;
  onModeChange: (mode: GameMode) => void;
  onNewGame: () => void;
  isV2?: boolean;  // 추가
}

// 컴포넌트 내부에 버전 전환 링크 추가
{isV2 ? (
  <a
    href="/"
    className="text-sm text-gray-500 hover:text-gray-700 font-medium flex items-center gap-1"
  >
    ← v1으로 돌아가기
  </a>
) : (
  <a
    href="/v2"
    className="text-sm text-purple-500 hover:text-purple-700 font-medium flex items-center gap-1"
  >
    v2 체험하기 →
    <span className="px-1.5 py-0.5 bg-purple-100 text-purple-600 text-xs rounded-full">Beta</span>
  </a>
)}
```

### Step 2: 테스트

Expected:
- v1 페이지(/)에서 "v2 체험하기 →" 링크 표시
- v2 페이지(/v2)에서 "← v1으로 돌아가기" 링크 표시

### Step 3: 커밋

```bash
git add components/Header.tsx
git commit -m "feat(frontend): add version toggle link in header"
```

---

## 완료 체크리스트

- [ ] Task 3.1: V2 타입 정의 및 페이지 기본 구조
- [ ] Task 3.2: SettingsPanelV2 컴포넌트
- [ ] Task 3.3: useGenerateV2 훅 (API 연동)
- [ ] Task 3.4: SentenceListV2 (하이라이트)
- [ ] Task 3.5: 버전 전환 UI

---

## 다음 단계

Phase 3 완료 후 Phase 4 (통합 및 배포)로 진행:
- Task 4.1: 프론트-백 통합 테스트
- Task 4.2: Tracing 설정
- Task 4.3: 백엔드 배포
- Task 4.4: 프론트엔드 배포
