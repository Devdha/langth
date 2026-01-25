"use client";

import { motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import { ContrastSet, LanguageV2 } from "@/types/v2";

interface ContrastSetCardProps {
  set: ContrastSet;
  index: number;
  language: LanguageV2;
}

const labelStyles = {
  target: "bg-amber-100 text-amber-800 border-amber-200",
  contrast: "bg-sky-100 text-sky-800 border-sky-200",
};

function getSentenceText(sentence: ContrastSet["targetSentence"]) {
  if (sentence?.text) return sentence.text;
  if (sentence?.tokens?.length) return sentence.tokens.join(" ");
  return "";
}

export default function ContrastSetCard({ set, index, language }: ContrastSetCardProps) {
  const targetText = getSentenceText(set.targetSentence);
  const contrastText = getSentenceText(set.contrastSentence);
  const targetWord = set.targetWord || "목표";
  const contrastWord = set.contrastWord || "대조";

  const handlePlay = (text: string) => {
    if (!text) return;
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === "en" ? "en-US" : "ko-KR";
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      transition={{
        duration: 0.35,
        delay: index * 0.04,
        type: "spring",
        bounce: 0.35,
      }}
      className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden hover:shadow-2xl hover:border-primary/30 transition-all"
    >
      <div className="p-6 space-y-4">
        <div className="flex flex-wrap gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${labelStyles.target}`}>
            목표: {targetWord}
          </span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${labelStyles.contrast}`}>
            대조: {contrastWord}
          </span>
        </div>

        <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-amber-700">목표 문장</span>
            <button
              onClick={() => handlePlay(targetText)}
              className="p-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors"
              title="읽어보기"
              aria-label="목표 문장 읽어보기"
            >
              <Volume2 size={16} />
            </button>
          </div>
          <p className="text-lg font-semibold text-gray-800 leading-snug break-keep">
            {targetText || "문장을 생성하지 못했어요."}
          </p>
        </div>

        <div className="rounded-xl border border-sky-100 bg-sky-50/50 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-sky-700">대조 문장</span>
            <button
              onClick={() => handlePlay(contrastText)}
              className="p-2 bg-sky-100 text-sky-700 rounded-lg hover:bg-sky-200 transition-colors"
              title="읽어보기"
              aria-label="대조 문장 읽어보기"
            >
              <Volume2 size={16} />
            </button>
          </div>
          <p className="text-lg font-semibold text-gray-800 leading-snug break-keep">
            {contrastText || "문장을 생성하지 못했어요."}
          </p>
        </div>
      </div>

      <div className="h-2 bg-gradient-to-r from-amber-400 via-primary to-sky-400" />
    </motion.div>
  );
}
