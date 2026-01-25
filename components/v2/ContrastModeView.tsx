"use client";

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2 } from "lucide-react";

// Types for minimal pairs data
interface WordPair {
  word1: string;
  word2: string;
  meaning1: string;
  meaning2: string;
}

// Import the minimal pairs data
import koreanMinimalPairs from "@/backend/app/data/korean_minimal_pairs.json";
import englishMinimalPairs from "@/backend/app/data/english_minimal_pairs.json";

// Category metadata by language
const CATEGORIES_KO = [
  { id: "aspirationContrast", label: "기식성", desc: "평음-격음" },
  { id: "tensionContrast", label: "긴장성", desc: "평음-경음" },
  { id: "placeContrast", label: "조음위치", desc: "조음 위치 대립" },
  { id: "mannerContrast", label: "조음방법", desc: "조음 방법 대립" },
  { id: "finalConsonant", label: "종성", desc: "받침 대립" },
  { id: "vowelContrast", label: "모음", desc: "모음 대립" },
] as const;

const CATEGORIES_EN = [
  { id: "voicingContrast", label: "Voicing", desc: "Voiced vs Voiceless" },
  { id: "placeContrast", label: "Place", desc: "Place of Articulation" },
  { id: "mannerContrast", label: "Manner", desc: "Manner of Articulation" },
  { id: "finalConsonant", label: "Final", desc: "Word-final Consonants" },
  { id: "clusterReduction", label: "Clusters", desc: "Consonant Clusters" },
  { id: "vowelContrast", label: "Vowels", desc: "Vowel Contrasts" },
] as const;

interface ContrastModeViewProps {
  language?: "ko" | "en";
}

export default function ContrastModeView({ language: initialLanguage = "ko" }: ContrastModeViewProps) {
  // Local language state for independent control
  const [currentLanguage, setCurrentLanguage] = useState<"ko" | "en">(initialLanguage);

  // Get data and categories based on language
  const minimalPairsData = currentLanguage === "en" ? englishMinimalPairs : koreanMinimalPairs;
  const categories = currentLanguage === "en" ? CATEGORIES_EN : CATEGORIES_KO;
  const defaultCategory = currentLanguage === "en" ? "voicingContrast" : "aspirationContrast";

  const [selectedCategory, setSelectedCategory] = useState<string>(defaultCategory);
  const [selectedPhonemePair, setSelectedPhonemePair] = useState<string | null>(null);

  // Reset category when language changes
  useEffect(() => {
    setSelectedCategory(defaultCategory);
    setSelectedPhonemePair(null);
  }, [currentLanguage, defaultCategory]);

  // Get phoneme pairs for selected category
  const phonemePairs = useMemo(() => {
    const category = (minimalPairsData.minimalPairs as Record<string, unknown>)[selectedCategory] as Record<string, unknown> | undefined;
    if (!category) return [];

    return Object.keys(category).filter(key => key !== "_description");
  }, [selectedCategory, minimalPairsData]);

  // Auto-select first phoneme pair when category changes
  useEffect(() => {
    if (phonemePairs.length > 0) {
      setSelectedPhonemePair(phonemePairs[0]);
    }
  }, [phonemePairs]);

  // Get word pairs for selected phoneme pair
  const wordPairs = useMemo((): WordPair[] => {
    if (!selectedPhonemePair) return [];

    const category = (minimalPairsData.minimalPairs as Record<string, unknown>)[selectedCategory] as Record<string, unknown> | undefined;
    if (!category) return [];

    const phonemePairData = category[selectedPhonemePair] as { pairs?: WordPair[] } | undefined;
    if (!phonemePairData || typeof phonemePairData === "string") return [];

    return phonemePairData.pairs || [];
  }, [selectedCategory, selectedPhonemePair, minimalPairsData]);

  // Handle category change
  const handleCategoryChange = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setSelectedPhonemePair(null); // Reset phoneme pair selection
  };

  // TTS function
  const speak = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = currentLanguage === "en" ? "en-US" : "ko-KR";
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Labels based on language
  const labels = {
    categoryTitle: currentLanguage === "en" ? "Contrast Type" : "대립 유형 선택",
    phonemeTitle: currentLanguage === "en" ? "Phoneme Pair" : "음소쌍 선택",
    cardTitle: currentLanguage === "en" ? "Word Pairs" : "단어쌍 카드",
    count: currentLanguage === "en" ? " pairs" : "개",
    playBoth: currentLanguage === "en" ? "Play Both" : "둘 다 듣기",
    selectPrompt: currentLanguage === "en" ? "Select a phoneme pair" : "음소쌍을 선택해주세요",
  };

  return (
    <div className="space-y-6">
      {/* Language Toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-700">
          {currentLanguage === "en" ? "Word Pair Training" : "단어쌍 변별 훈련"}
        </h2>
        <div className="flex bg-gray-100 rounded-full p-1">
          <button
            onClick={() => setCurrentLanguage("ko")}
            className={`px-4 py-1.5 rounded-full text-sm font-bold transition-all ${
              currentLanguage === "ko"
                ? "bg-white text-pink-600 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            한국어
          </button>
          <button
            onClick={() => setCurrentLanguage("en")}
            className={`px-4 py-1.5 rounded-full text-sm font-bold transition-all ${
              currentLanguage === "en"
                ? "bg-white text-pink-600 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            English
          </button>
        </div>
      </div>

      {/* Category Selector */}
      <div>
        <h3 className="text-sm font-bold text-gray-500 mb-3">{labels.categoryTitle}</h3>
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-2 px-2">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => handleCategoryChange(category.id)}
              className={`flex-shrink-0 px-4 py-2 rounded-full font-bold text-sm transition-all ${
                selectedCategory === category.id
                  ? "bg-pink-500 text-white shadow-md"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2">
          {categories.find(c => c.id === selectedCategory)?.desc}
        </p>
      </div>

      {/* Phoneme Pair Selector */}
      <div>
        <h3 className="text-sm font-bold text-gray-500 mb-3">{labels.phonemeTitle}</h3>
        <div className="flex flex-wrap gap-2">
          {phonemePairs.map((pair) => (
            <button
              key={pair}
              onClick={() => setSelectedPhonemePair(pair)}
              className={`px-4 py-2 rounded-xl font-bold text-sm transition-all border-2 ${
                selectedPhonemePair === pair
                  ? "border-pink-500 bg-pink-50 text-pink-600"
                  : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
              }`}
            >
              {pair}
            </button>
          ))}
        </div>
      </div>

      {/* Word Pairs Grid */}
      <div>
        <h3 className="text-sm font-bold text-gray-500 mb-3">
          {labels.cardTitle}
          <span className="font-normal text-gray-400 ml-2">
            {wordPairs.length}{labels.count}
          </span>
        </h3>
        <AnimatePresence mode="popLayout">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {wordPairs.map((pair, index) => (
              <motion.div
                key={`${selectedPhonemePair}-${pair.word1}-${pair.word2}`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ delay: index * 0.03 }}
                className="bg-white rounded-2xl border-2 border-gray-100 p-4 hover:border-pink-200 hover:shadow-lg transition-all group"
              >
                {/* Word Pair Display */}
                <div className="flex items-center justify-center gap-3 mb-3">
                  <button
                    onClick={() => speak(pair.word1)}
                    className="text-2xl font-bold text-gray-800 hover:text-pink-500 transition-colors"
                  >
                    {pair.word1}
                  </button>
                  <span className="text-gray-300 text-xl">/</span>
                  <button
                    onClick={() => speak(pair.word2)}
                    className="text-2xl font-bold text-gray-800 hover:text-pink-500 transition-colors"
                  >
                    {pair.word2}
                  </button>
                </div>

                {/* Meanings */}
                <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
                  <span>{pair.meaning1}</span>
                  <span>/</span>
                  <span>{pair.meaning2}</span>
                </div>

                {/* Play Both Button */}
                <button
                  onClick={() => {
                    speak(pair.word1);
                    setTimeout(() => speak(pair.word2), 800);
                  }}
                  className="w-full mt-3 py-2 rounded-lg bg-gray-50 text-gray-400 hover:bg-pink-50 hover:text-pink-500 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100"
                >
                  <Volume2 size={16} />
                  <span className="text-xs font-bold">{labels.playBoth}</span>
                </button>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>

        {wordPairs.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <div className="text-4xl mb-2">📭</div>
            <p>{labels.selectPrompt}</p>
          </div>
        )}
      </div>
    </div>
  );
}
