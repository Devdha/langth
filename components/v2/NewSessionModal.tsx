"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, User, Palette } from "lucide-react";
import { SessionColor } from "@/types/v2";

interface NewSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, patientName: string, color: SessionColor) => void;
}

const COLORS: { id: SessionColor; label: string; class: string }[] = [
  { id: "purple", label: "보라", class: "bg-purple-500" },
  { id: "pink", label: "분홍", class: "bg-pink-500" },
  { id: "blue", label: "파랑", class: "bg-blue-500" },
  { id: "green", label: "초록", class: "bg-emerald-500" },
  { id: "orange", label: "주황", class: "bg-orange-500" },
  { id: "red", label: "빨강", class: "bg-red-500" },
];

export default function NewSessionModal({
  isOpen,
  onClose,
  onCreate,
}: NewSessionModalProps) {
  const [sessionName, setSessionName] = useState("");
  const [patientName, setPatientName] = useState("");
  const [selectedColor, setSelectedColor] = useState<SessionColor>("purple");

  const handleCreate = () => {
    if (!sessionName.trim()) {
      alert("세션 이름을 입력해주세요");
      return;
    }
    onCreate(sessionName.trim(), patientName.trim(), selectedColor);
    // Reset form
    setSessionName("");
    setPatientName("");
    setSelectedColor("purple");
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
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Sparkles size={24} />
                  새 세션 만들기
                </h2>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-full transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
              <p className="text-white/80 text-sm mt-2">
                치료 세션의 이름과 정보를 입력하세요
              </p>
            </div>

            {/* Form */}
            <div className="p-6 space-y-6">
              {/* Session Name */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  세션 이름 *
                </label>
                <input
                  type="text"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  placeholder="예: 홍길동 - ㄹ 연습"
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:outline-none transition-colors"
                  autoFocus
                />
              </div>

              {/* Patient Name */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                  <User size={16} />
                  환자/아동 이름 (선택)
                </label>
                <input
                  type="text"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="예: 홍길동"
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:outline-none transition-colors"
                />
              </div>

              {/* Color Selection */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                  <Palette size={16} />
                  세션 색상
                </label>
                <div className="flex gap-3 justify-center">
                  {COLORS.map((color) => (
                    <button
                      key={color.id}
                      onClick={() => setSelectedColor(color.id)}
                      className={`w-10 h-10 rounded-full ${color.class} transition-all ${
                        selectedColor === color.id
                          ? "ring-4 ring-offset-2 ring-purple-300 scale-110"
                          : "hover:scale-105"
                      }`}
                      title={color.label}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-6 py-3 rounded-xl font-bold text-gray-500 hover:bg-gray-100 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleCreate}
                disabled={!sessionName.trim()}
                className="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                만들기
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
