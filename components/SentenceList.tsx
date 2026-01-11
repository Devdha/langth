"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Trash2, Edit2, Volume2 } from "lucide-react";
import { TherapyItem } from "@/types";

interface SentenceListProps {
  items: TherapyItem[];
  onDelete: (id: string) => void;
  onEdit: (item: TherapyItem) => void;
  onPlay: (item: TherapyItem) => void;
}

export default function SentenceList({ items, onDelete, onEdit, onPlay }: SentenceListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center opacity-60">
        <div className="text-6xl mb-4">📭</div>
        <h3 className="text-2xl font-bold text-gray-400">문장이 없어요!</h3>
        <p className="text-gray-400">새로 만들기 버튼을 눌러 문장을 만들어보세요.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4 pb-24">
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
            transition={{ duration: 0.4, delay: index * 0.05, type: "spring", bounce: 0.4 }}
            className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden hover:shadow-xl hover:border-primary/30 transition-all group"
          >
            <div className="p-6 relative">
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                <button
                  onClick={() => onEdit(item)}
                  className="p-2 bg-gray-100 text-gray-500 rounded-lg hover:bg-info hover:text-white transition-colors"
                  title="수정"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={() => onDelete(item.id)}
                  className="p-2 bg-gray-100 text-gray-500 rounded-lg hover:bg-warning hover:text-white transition-colors"
                  title="삭제"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              
              <div className="mb-2 flex gap-2">
                {item.targetPhoneme && (
                  <span className="bg-secondary/10 text-secondary px-3 py-1 rounded-full text-sm font-bold">
                    {item.targetPhoneme}
                  </span>
                )}
                <span className="bg-gray-100 text-gray-500 px-3 py-1 rounded-full text-sm font-bold">
                  {item.wordCount}어절
                </span>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-800 leading-snug break-keep mt-4 mb-4">
                {item.text}
              </h3>
              
              <button
                onClick={() => onPlay(item)}
                className="w-full bg-primary/10 hover:bg-primary hover:text-white text-primary font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95"
              >
                <Volume2 size={20} />
                <span>읽어보기</span>
              </button>
            </div>
            
            <div className="h-2 bg-gradient-to-r from-primary via-secondary to-accent" />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
