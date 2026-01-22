"use client";

import { motion } from "framer-motion";
import { Volume2, Edit2, Trash2 } from "lucide-react";
import { TherapyItemV2 } from "@/types/v2";
import HighlightedText from "./HighlightedText";

interface SentenceCardV2Props {
  item: TherapyItemV2;
  index: number;
  onPlay: (item: TherapyItemV2) => void;
  onEdit: (item: TherapyItemV2) => void;
  onDelete: (id: string) => void;
}

// Diagnosis color mapping
const diagnosisColors = {
  SSD: "bg-blue-100 text-blue-700 border-blue-200",
  ASD: "bg-purple-100 text-purple-700 border-purple-200",
  LD: "bg-green-100 text-green-700 border-green-200",
};

// Position labels in Korean
const positionLabels = {
  onset: "초성",
  nucleus: "중성",
  coda: "종성",
  any: "전체",
};

export default function SentenceCardV2({
  item,
  index,
  onPlay,
  onEdit,
  onDelete,
}: SentenceCardV2Props) {
  const scorePercentage = Math.round(item.score * 100);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        type: "spring",
        bounce: 0.4,
      }}
      className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden hover:shadow-2xl hover:border-primary/30 transition-all group relative"
    >
      {/* Action buttons - visible on hover */}
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2 z-10">
        <button
          onClick={() => onPlay(item)}
          className="p-2 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-white transition-colors"
          title="읽어보기"
          aria-label="읽어보기"
        >
          <Volume2 size={16} />
        </button>
        <button
          onClick={() => onEdit(item)}
          className="p-2 bg-gray-100 text-gray-500 rounded-lg hover:bg-info hover:text-white transition-colors"
          title="수정"
          aria-label="수정"
        >
          <Edit2 size={16} />
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="p-2 bg-gray-100 text-gray-500 rounded-lg hover:bg-warning hover:text-white transition-colors"
          title="삭제"
          aria-label="삭제"
        >
          <Trash2 size={16} />
        </button>
      </div>

      <div className="p-6">
        {/* Top badges: Diagnosis and Target */}
        <div className="mb-4 flex flex-wrap gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${
              diagnosisColors[item.diagnosis]
            }`}
          >
            {item.diagnosis}
          </span>
          {item.target ? (
            <span className="bg-gradient-to-r from-yellow-100 to-amber-100 text-amber-800 px-3 py-1 rounded-full text-xs font-bold border border-amber-200">
              {item.target.phoneme} · {positionLabels[item.target.position]}
            </span>
          ) : (
            <span className="bg-gradient-to-r from-pink-100 to-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-bold border border-purple-200">
              핵심어휘
            </span>
          )}
        </div>

        {/* Sentence with highlighting */}
        <h3 className="text-2xl font-bold text-gray-800 leading-snug break-keep mb-4">
          <HighlightedText text={item.text} matchedWords={item.matchedWords} />
        </h3>

        {/* Score progress bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-gray-500">적합도</span>
            <span className="text-xs font-bold text-gray-700">{scorePercentage}%</span>
          </div>
          <div
            className="w-full bg-gray-200 rounded-full h-2 overflow-hidden"
            role="progressbar"
            aria-valuenow={scorePercentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="적합도"
          >
            <div
              className="h-full bg-gradient-to-r from-primary via-secondary to-accent transition-all duration-500"
              style={{ width: `${scorePercentage}%` }}
            />
          </div>
        </div>

        {/* Metadata row */}
        <div className="flex items-center gap-3 text-xs text-gray-500 font-medium">
          <span className="flex items-center gap-1">
            <span className="font-bold">{item.wordCount}</span> 어절
          </span>
          {item.function && (
            <>
              <span>•</span>
              <span className="bg-gray-100 px-2 py-0.5 rounded-md">
                {item.function}
              </span>
            </>
          )}
          <span>•</span>
          <span className="flex items-center gap-1">
            <span className="font-bold">{item.matchedWords.length}</span> 매칭
          </span>
        </div>
      </div>

      {/* Bottom accent strip */}
      <div className="h-2 bg-gradient-to-r from-primary via-secondary to-accent" />
    </motion.div>
  );
}
