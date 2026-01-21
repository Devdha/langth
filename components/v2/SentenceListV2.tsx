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

export default function SentenceListV2({
  items,
  onDelete,
  onEdit,
  onPlay,
}: SentenceListV2Props) {
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
          <SentenceCardV2
            key={item.id}
            item={item}
            index={index}
            onPlay={onPlay}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
