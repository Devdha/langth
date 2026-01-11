"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Star } from "lucide-react";
import { GameSettings } from "@/types";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (settings: GameSettings) => void;
  initialSettings?: GameSettings;
}

const PHONEMES = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
const THEMES = [
  { id: '', label: '없음', icon: '✨', color: 'bg-gray-400' },
  { id: 'daily', label: '일상', icon: '🏠', color: 'bg-info' },
  { id: 'food', label: '음식', icon: '🍽️', color: 'bg-success' },
  { id: 'animal', label: '동물', icon: '🐶', color: 'bg-warning' },
  { id: 'family', label: '가족', icon: '👨‍👩‍👧', color: 'bg-purple' },
];

const COUNTS = [5, 10, 15, 20];
const LANGUAGES = [
  { id: 'ko', label: '한국어', icon: '🇰🇷' },
  { id: 'en', label: 'English', icon: '🇺🇸' },
];
const AGES = [
  { id: 3, label: '만 3세', desc: '기본 어휘' },
  { id: 4, label: '만 4세', desc: '일상 어휘' },
  { id: 5, label: '만 5세', desc: '확장 어휘' },
  { id: 6, label: '만 6세', desc: '학령기 준비' },
  { id: 7, label: '만 7세', desc: '초등 저학년' },
];

export default function SettingsPanel({ isOpen, onClose, onGenerate, initialSettings }: SettingsPanelProps) {
  const [phoneme, setPhoneme] = useState(initialSettings?.phoneme || '');
  const [level, setLevel] = useState(initialSettings?.level || 2);
  const [theme, setTheme] = useState(initialSettings?.theme || 'daily');
  const [count, setCount] = useState(initialSettings?.count || 10);
  const [language, setLanguage] = useState<'ko' | 'en'>(initialSettings?.language || 'ko');
  const [age, setAge] = useState<3|4|5|6|7>(initialSettings?.age || 4);

  const handleGenerate = () => {
    onGenerate({ phoneme, level: level as 2|3|4|5|6, theme, count, language, age });
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
              className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden border-4 border-primary/20"
            >
              <div className="bg-primary/10 p-6 flex justify-between items-center border-b-2 border-primary/10">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <span className="text-3xl">⚙️</span> 설정하기
                </h2>
                <button 
                  onClick={onClose}
                  className="p-2 hover:bg-black/5 rounded-full transition-colors"
                >
                  <X size={24} className="text-gray-500" />
                </button>
              </div>

              <div className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                
                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-secondary text-white flex items-center justify-center text-sm">1</span>
                    연습할 소리를 골라보세요 (음소)
                  </h3>
                  <div className="grid grid-cols-5 sm:grid-cols-8 gap-3">
                    <button
                      onClick={() => setPhoneme('')}
                      className={`aspect-square rounded-2xl text-sm font-bold transition-all transform hover:scale-105 active:scale-95 ${
                        phoneme === ''
                          ? 'bg-gray-500 text-white shadow-lg shadow-gray-500/30 ring-4 ring-gray-500/20'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border-2 border-transparent'
                      }`}
                    >
                      없음
                    </button>
                    {PHONEMES.map((p) => (
                      <button
                        key={p}
                        onClick={() => setPhoneme(p)}
                        className={`aspect-square rounded-2xl text-xl font-bold transition-all transform hover:scale-105 active:scale-95 ${
                          phoneme === p
                            ? 'bg-secondary text-white shadow-lg shadow-secondary/30 ring-4 ring-secondary/20'
                            : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border-2 border-transparent'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-sm">2</span>
                    문장이 얼마나 길까요? (어절)
                  </h3>
                  <div className="flex gap-4 justify-center">
                    {[2, 3, 4, 5, 6].map((n) => (
                      <button
                        key={n}
                        onClick={() => setLevel(n as 2 | 3 | 4 | 5 | 6)}
                        className={`w-14 h-14 rounded-full text-xl font-bold transition-all transform hover:scale-110 active:scale-90 flex items-center justify-center ${
                          level === n
                            ? 'bg-accent text-white shadow-lg shadow-accent/30 ring-4 ring-accent/20'
                            : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-info text-white flex items-center justify-center text-sm">3</span>
                    어떤 이야기를 할까요? (주제)
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {THEMES.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => setTheme(t.id)}
                        className={`p-4 rounded-2xl border-2 transition-all text-left relative overflow-hidden group ${
                          theme === t.id
                            ? 'border-transparent ring-4 ring-opacity-50'
                            : 'border-gray-100 hover:border-gray-200 bg-white'
                        } ${theme === t.id ? 'ring-' + t.color.replace('bg-', '') : ''}`}
                      >
                        <div className={`absolute inset-0 opacity-10 ${t.color}`} />
                        {theme === t.id && (
                          <div className={`absolute inset-0 opacity-20 ${t.color}`} />
                        )}
                        <div className="text-3xl mb-2 group-hover:scale-110 transition-transform origin-left">{t.icon}</div>
                        <div className="font-bold text-gray-700">{t.label}</div>
                      </button>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-teal-500 text-white flex items-center justify-center text-sm">4</span>
                    몇 살 친구예요? (연령)
                  </h3>
                  <div className="flex flex-wrap gap-3 justify-center">
                    {AGES.map((a) => (
                      <button
                        key={a.id}
                        onClick={() => setAge(a.id as 3|4|5|6|7)}
                        className={`px-4 py-3 rounded-2xl font-bold transition-all transform hover:scale-105 active:scale-95 flex flex-col items-center ${
                          age === a.id
                            ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/30 ring-4 ring-teal-500/20'
                            : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <span>{a.label}</span>
                        <span className={`text-xs ${age === a.id ? 'text-teal-100' : 'text-gray-400'}`}>{a.desc}</span>
                      </button>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-pink-500 text-white flex items-center justify-center text-sm">5</span>
                    몇 개 만들까요? (개수)
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

                <section>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm">6</span>
                    어떤 언어로? (언어)
                  </h3>
                  <div className="flex gap-4 justify-center">
                    {LANGUAGES.map((l) => (
                      <button
                        key={l.id}
                        onClick={() => setLanguage(l.id as 'ko' | 'en')}
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
                  className="px-8 py-3 rounded-xl font-bold text-white bg-primary shadow-lg hover:shadow-xl hover:bg-primary/90 transition-all transform hover:-translate-y-1 active:translate-y-0 flex items-center gap-2"
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
