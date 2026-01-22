"use client";

import { AnimatePresence } from "framer-motion";
import { ContrastSet, LanguageV2 } from "@/types/v2";
import ContrastSetCard from "./ContrastSetCard";

interface ContrastSetListProps {
  sets: ContrastSet[];
  language: LanguageV2;
}

export default function ContrastSetList({ sets, language }: ContrastSetListProps) {
  if (sets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center opacity-60">
        <div className="text-6xl mb-4">🧩</div>
        <h3 className="text-2xl font-bold text-gray-400">대조 세트가 없어요!</h3>
        <p className="text-gray-400">조건을 조정하고 다시 생성해보세요.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4 pb-24">
      <AnimatePresence mode="popLayout">
        {sets.map((set, index) => (
          <ContrastSetCard key={`${set.targetWord}-${set.contrastWord}-${index}`} set={set} index={index} language={language} />
        ))}
      </AnimatePresence>
    </div>
  );
}
