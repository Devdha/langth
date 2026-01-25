"use client";

import { PhonemePosition, LanguageV2 } from "@/types/v2";

interface PhonemeSelectorProps {
  language: LanguageV2;
  phoneme: string;
  position: PhonemePosition;
  minOccurrences: number;
  onPhonemeChange: (phoneme: string) => void;
  onPositionChange: (position: PhonemePosition) => void;
  onMinOccurrencesChange: (min: number) => void;
}

// Korean phonemes by position
const KOREAN_PHONEMES = {
  onset: ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'],
  nucleus: ['ㅏ', 'ㅓ', 'ㅗ', 'ㅜ', 'ㅡ', 'ㅣ', 'ㅐ', 'ㅔ', 'ㅚ', 'ㅟ'],
  coda: ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅇ'],
};

// English phonemes by position
const ENGLISH_PHONEMES = {
  onset: ['R', 'L', 'S', 'TH', 'SH', 'CH', 'K', 'G', 'F', 'V'],
  coda: ['R', 'L', 'S', 'Z', 'TH', 'NG', 'K', 'T'],
  nucleus: [],
};

const POSITIONS = [
  { id: 'onset' as const, label: '초성', desc: 'Initial' },
  { id: 'coda' as const, label: '종성', desc: 'Final' },
  { id: 'any' as const, label: '전체', desc: 'Any' },
];

const MIN_OCCURRENCES = [1, 2, 3];

export default function PhonemeSelector({
  language,
  phoneme,
  position,
  minOccurrences,
  onPhonemeChange,
  onPositionChange,
  onMinOccurrencesChange,
}: PhonemeSelectorProps) {
  // Get available phonemes based on language and position
  const getAvailablePhonemes = (): string[] => {
    if (position === 'any') {
      return language === 'ko'
        ? [...new Set([...KOREAN_PHONEMES.onset, ...KOREAN_PHONEMES.coda])]
        : [...new Set([...ENGLISH_PHONEMES.onset, ...ENGLISH_PHONEMES.coda])];
    }

    const phonemeMap = language === 'ko' ? KOREAN_PHONEMES : ENGLISH_PHONEMES;
    return phonemeMap[position] || [];
  };

  const handlePositionChange = (newPosition: PhonemePosition) => {
    onPositionChange(newPosition);

    // Reset phoneme if current phoneme is not available in new position
    const availablePhonemes = newPosition === 'any'
      ? (language === 'ko'
          ? [...new Set([...KOREAN_PHONEMES.onset, ...KOREAN_PHONEMES.coda])]
          : [...new Set([...ENGLISH_PHONEMES.onset, ...ENGLISH_PHONEMES.coda])])
      : (language === 'ko' ? KOREAN_PHONEMES : ENGLISH_PHONEMES)[newPosition] || [];

    if (phoneme && !availablePhonemes.includes(phoneme)) {
      onPhonemeChange(availablePhonemes[0] || '');
    }
  };

  const availablePhonemes = getAvailablePhonemes();

  return (
    <div className="space-y-6">
      {/* Position Selection */}
      <div>
        <h4 className="text-sm font-bold text-gray-600 mb-3">음소 위치</h4>
        <div className="flex gap-3">
          {POSITIONS.map((p) => (
            <button
              key={p.id}
              onClick={() => handlePositionChange(p.id)}
              className={`flex-1 p-3 rounded-xl border-2 transition-all ${
                position === p.id
                  ? 'border-pink-500 bg-pink-50 ring-2 ring-pink-200'
                  : 'border-gray-100 hover:border-gray-200 bg-white'
              }`}
            >
              <div className="font-bold text-gray-800 text-sm">{p.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Phoneme Selection */}
      <div>
        <h4 className="text-sm font-bold text-gray-600 mb-3">목표 음소</h4>
        <div className={`grid gap-3 ${language === 'ko' ? 'grid-cols-5 sm:grid-cols-8' : 'grid-cols-4 sm:grid-cols-6'}`}>
          {availablePhonemes.map((p) => (
            <button
              key={p}
              onClick={() => onPhonemeChange(p)}
              className={`aspect-square rounded-2xl font-bold transition-all transform hover:scale-105 active:scale-95 ${
                language === 'ko' ? 'text-xl' : 'text-sm'
              } ${
                phoneme === p
                  ? 'bg-pink-500 text-white shadow-lg shadow-pink-500/30 ring-4 ring-pink-500/20'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border-2 border-transparent'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Min Occurrences */}
      <div>
        <h4 className="text-sm font-bold text-gray-600 mb-3">최소 출현 횟수</h4>
        <div className="flex gap-4 justify-center">
          {MIN_OCCURRENCES.map((n) => (
            <button
              key={n}
              onClick={() => onMinOccurrencesChange(n)}
              className={`w-14 h-14 rounded-full text-lg font-bold transition-all transform hover:scale-110 active:scale-90 flex items-center justify-center ${
                minOccurrences === n
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30 ring-4 ring-purple-500/20'
                  : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
