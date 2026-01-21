"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Star } from "lucide-react";
import { GameSettingsV2, LanguageV2, CommunicativeFunction } from "@/types/v2";
import DiagnosisSelector from "./DiagnosisSelector";
import PhonemeSelector from "./PhonemeSelector";

interface SettingsPanelV2Props {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (settings: GameSettingsV2) => void;
  initialSettings?: GameSettingsV2;
}

const THEMES = [
  { id: '', label: '없음', icon: '✨', color: 'bg-gray-400' },
  { id: 'daily', label: '일상', icon: '🏠', color: 'bg-info' },
  { id: 'food', label: '음식', icon: '🍽️', color: 'bg-success' },
  { id: 'animal', label: '동물', icon: '🐶', color: 'bg-warning' },
  { id: 'family', label: '가족', icon: '👨‍👩‍👧', color: 'bg-purple-500' },
];

const COMMUNICATIVE_FUNCTIONS = [
  { id: null, label: '없음', icon: '✨', desc: 'None' },
  { id: 'request' as const, label: '요청', icon: '🙋', desc: 'Request' },
  { id: 'reject' as const, label: '거절', icon: '🚫', desc: 'Reject' },
  { id: 'help' as const, label: '도움', icon: '🆘', desc: 'Help' },
  { id: 'choice' as const, label: '선택', icon: '🤔', desc: 'Choice' },
  { id: 'attention' as const, label: '주목', icon: '👋', desc: 'Attention' },
  { id: 'question' as const, label: '질문', icon: '❓', desc: 'Question' },
];

const COUNTS = [5, 10, 15, 20];
const LANGUAGES = [
  { id: 'ko' as const, label: '한국어', icon: '🇰🇷' },
  { id: 'en' as const, label: 'English', icon: '🇺🇸' },
];
const AGES = [
  { id: 3, label: '만 3세', desc: '기본 어휘' },
  { id: 4, label: '만 4세', desc: '일상 어휘' },
  { id: 5, label: '만 5세', desc: '확장 어휘' },
  { id: 6, label: '만 6세', desc: '학령기 준비' },
  { id: 7, label: '만 7세', desc: '초등 저학년' },
];

export default function SettingsPanelV2({
  isOpen,
  onClose,
  onGenerate,
  initialSettings
}: SettingsPanelV2Props) {
  const [diagnosis, setDiagnosis] = useState(initialSettings?.diagnosis || 'SSD');
  const [therapyApproach, setTherapyApproach] = useState(initialSettings?.therapyApproach || 'minimal_pairs');
  const [phoneme, setPhoneme] = useState(initialSettings?.target.phoneme || 'ㄹ');
  const [position, setPosition] = useState(initialSettings?.target.position || 'onset');
  const [minOccurrences, setMinOccurrences] = useState(initialSettings?.target.minOccurrences || 1);
  const [sentenceLength, setSentenceLength] = useState(initialSettings?.sentenceLength || 3);
  const [theme, setTheme] = useState(initialSettings?.theme || '');
  const [communicativeFunction, setCommunicativeFunction] = useState<CommunicativeFunction | null>(
    initialSettings?.communicativeFunction || null
  );
  const [age, setAge] = useState<3 | 4 | 5 | 6 | 7>(initialSettings?.age || 4);
  const [language, setLanguage] = useState<LanguageV2>(initialSettings?.language || 'ko');
  const [count, setCount] = useState(initialSettings?.count || 10);

  const handleGenerate = () => {
    const settings: GameSettingsV2 = {
      language,
      age,
      count,
      target: {
        phoneme,
        position,
        minOccurrences,
      },
      sentenceLength,
      diagnosis,
      therapyApproach,
      theme,
      communicativeFunction,
    };
    onGenerate(settings);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
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
                  <span className="text-3xl">⚙️</span> V2 설정하기
                </h2>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-black/5 rounded-full transition-colors"
                >
                  <X size={24} className="text-gray-500" />
                </button>
              </div>

              <div className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">

                {/* Section 1: Diagnosis & Therapy Approach */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center text-sm">1</span>
                    진단군 및 접근법
                  </h3>
                  <DiagnosisSelector
                    diagnosis={diagnosis}
                    therapyApproach={therapyApproach}
                    onDiagnosisChange={setDiagnosis}
                    onApproachChange={setTherapyApproach}
                  />
                </section>

                {/* Section 2: Target Phoneme */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-pink-500 text-white flex items-center justify-center text-sm">2</span>
                    목표 음소
                  </h3>
                  <PhonemeSelector
                    language={language}
                    phoneme={phoneme}
                    position={position}
                    minOccurrences={minOccurrences}
                    onPhonemeChange={setPhoneme}
                    onPositionChange={setPosition}
                    onMinOccurrencesChange={setMinOccurrences}
                  />
                </section>

                {/* Section 3: Sentence Length */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm">3</span>
                    문장 길이 (어절)
                  </h3>
                  <div className="flex gap-4 justify-center">
                    {[2, 3, 4, 5, 6].map((n) => (
                      <button
                        key={n}
                        onClick={() => setSentenceLength(n)}
                        className={`w-14 h-14 rounded-full text-xl font-bold transition-all transform hover:scale-110 active:scale-90 flex items-center justify-center ${
                          sentenceLength === n
                            ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 ring-4 ring-indigo-500/20'
                            : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </section>

                {/* Section 4: Theme & Communicative Function */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-teal-500 text-white flex items-center justify-center text-sm">4</span>
                    주제 및 의사소통 기능
                  </h3>

                  {/* Theme */}
                  <div className="mb-4">
                    <h4 className="text-sm font-bold text-gray-600 mb-3">주제</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      {THEMES.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setTheme(t.id)}
                          className={`p-3 rounded-2xl border-2 transition-all text-center relative overflow-hidden group ${
                            theme === t.id
                              ? 'border-transparent ring-4 ring-opacity-50'
                              : 'border-gray-100 hover:border-gray-200 bg-white'
                          } ${theme === t.id ? 'ring-' + t.color.replace('bg-', '') : ''}`}
                        >
                          <div className={`absolute inset-0 opacity-10 ${t.color}`} />
                          {theme === t.id && (
                            <div className={`absolute inset-0 opacity-20 ${t.color}`} />
                          )}
                          <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">{t.icon}</div>
                          <div className="font-bold text-gray-700 text-xs">{t.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Communicative Function */}
                  <div>
                    <h4 className="text-sm font-bold text-gray-600 mb-3">의사소통 기능</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {COMMUNICATIVE_FUNCTIONS.map((f) => (
                        <button
                          key={f.id || 'none'}
                          onClick={() => setCommunicativeFunction(f.id)}
                          className={`p-3 rounded-xl border-2 transition-all text-center ${
                            communicativeFunction === f.id
                              ? 'border-teal-500 bg-teal-50 ring-2 ring-teal-200'
                              : 'border-gray-100 hover:border-gray-200 bg-white'
                          }`}
                        >
                          <div className="text-xl mb-1">{f.icon}</div>
                          <div className="font-bold text-gray-700 text-xs">{f.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </section>

                {/* Section 5: Age & Language */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm">5</span>
                    연령 및 언어
                  </h3>

                  {/* Age */}
                  <div className="mb-4">
                    <h4 className="text-sm font-bold text-gray-600 mb-3">연령</h4>
                    <div className="flex flex-wrap gap-3 justify-center">
                      {AGES.map((a) => (
                        <button
                          key={a.id}
                          onClick={() => setAge(a.id as 3 | 4 | 5 | 6 | 7)}
                          className={`px-4 py-3 rounded-2xl font-bold transition-all transform hover:scale-105 active:scale-95 flex flex-col items-center ${
                            age === a.id
                              ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30 ring-4 ring-orange-500/20'
                              : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          <span>{a.label}</span>
                          <span className={`text-xs ${age === a.id ? 'text-orange-100' : 'text-gray-400'}`}>{a.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Language */}
                  <div>
                    <h4 className="text-sm font-bold text-gray-600 mb-3">언어</h4>
                    <div className="flex gap-4 justify-center">
                      {LANGUAGES.map((l) => (
                        <button
                          key={l.id}
                          onClick={() => setLanguage(l.id)}
                          className={`px-6 py-3 rounded-2xl font-bold transition-all transform hover:scale-105 active:scale-95 flex items-center gap-2 ${
                            language === l.id
                              ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 ring-4 ring-indigo-500/20'
                              : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          <span className="text-xl">{l.icon}</span>
                          {l.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </section>

                {/* Section 6: Count */}
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-pink-500 text-white flex items-center justify-center text-sm">6</span>
                    생성 개수
                  </h3>
                  <div className="flex gap-4 justify-center">
                    {COUNTS.map((n) => (
                      <button
                        key={n}
                        onClick={() => setCount(n)}
                        className={`w-14 h-14 rounded-full text-lg font-bold transition-all transform hover:scale-110 active:scale-90 flex items-center justify-center ${
                          count === n
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
                  className="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg hover:shadow-xl hover:from-purple-600 hover:to-pink-600 transition-all transform hover:-translate-y-1 active:translate-y-0 flex items-center gap-2"
                >
                  <Star className="fill-white" size={20} />
                  문장 만들기
                </button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
