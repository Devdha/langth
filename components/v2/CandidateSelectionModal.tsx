"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, Edit2, Search, SortDesc } from "lucide-react";
import { TherapyItemV2 } from "@/types/v2";
import HighlightedText from "./HighlightedText";

interface CandidateSelectionModalProps {
  isOpen: boolean;
  candidates: TherapyItemV2[];
  requestedCount: number;
  onClose: () => void;
  onConfirm: (selected: TherapyItemV2[]) => void;
}

const difficultyLabels: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

const difficultyColors: Record<string, string> = {
  easy: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  hard: "bg-rose-100 text-rose-700",
};

type SortOption = "score" | "difficulty" | "text";

export default function CandidateSelectionModal({
  isOpen,
  candidates,
  requestedCount,
  onClose,
  onConfirm,
}: CandidateSelectionModalProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editedTexts, setEditedTexts] = useState<Map<string, string>>(new Map());
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("score");

  // Filter and sort candidates
  const filteredCandidates = useMemo(() => {
    let filtered = candidates;

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c => c.text.toLowerCase().includes(query));
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "score":
          return b.score - a.score;
        case "difficulty":
          const diffOrder = { easy: 0, medium: 1, hard: 2 };
          return (diffOrder[a.difficulty || "medium"] || 1) - (diffOrder[b.difficulty || "medium"] || 1);
        case "text":
          return a.text.localeCompare(b.text, "ko");
        default:
          return 0;
      }
    });

    return sorted;
  }, [candidates, searchQuery, sortBy]);

  const handleToggle = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filteredCandidates.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredCandidates.map(c => c.id)));
    }
  };

  const handleStartEdit = (candidate: TherapyItemV2) => {
    setEditingId(candidate.id);
    // Use edited text if exists, otherwise original
    setEditText(editedTexts.get(candidate.id) ?? candidate.text);
  };

  // Get display text for a candidate (edited or original)
  const getDisplayText = (candidate: TherapyItemV2) => {
    return editedTexts.get(candidate.id) ?? candidate.text;
  };

  const handleSaveEdit = () => {
    if (!editingId) return;
    // Save edited text to map
    const trimmed = editText.trim();
    setEditedTexts(prev => new Map(prev).set(editingId, trimmed));
    setEditingId(null);
  };

  const handleConfirm = () => {
    const selected = candidates
      .filter(c => selectedIds.has(c.id))
      .map(c => {
        const editedText = editedTexts.get(c.id);
        if (editedText !== undefined) {
          return { ...c, text: editedText, wordCount: editedText.split(/\s+/).length };
        }
        return c;
      });
    onConfirm(selected);
  };

  const selectedCount = selectedIds.size;

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
            className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-primary to-secondary p-6 text-white shrink-0">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Check size={24} />
                  문장 선택하기
                </h2>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-full transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
              <p className="text-white/80 text-sm mt-2">
                {candidates.length}개의 후보 중에서 사용할 문장을 선택하세요 (요청: {requestedCount}개)
              </p>
            </div>

            {/* Toolbar */}
            <div className="p-4 border-b border-gray-100 flex flex-wrap gap-3 items-center shrink-0">
              {/* Search */}
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="문장 검색..."
                  className="w-full pl-10 pr-4 py-2 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors text-sm"
                />
              </div>

              {/* Sort */}
              <div className="flex items-center gap-2">
                <SortDesc size={18} className="text-gray-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="px-3 py-2 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors text-sm"
                >
                  <option value="score">적합도순</option>
                  <option value="difficulty">난이도순</option>
                  <option value="text">가나다순</option>
                </select>
              </div>

              {/* Select All */}
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 rounded-xl border-2 border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors text-sm font-medium"
              >
                {selectedIds.size === filteredCandidates.length ? "전체 해제" : "전체 선택"}
              </button>
            </div>

            {/* Candidate List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {filteredCandidates.map((candidate, index) => (
                <motion.div
                  key={candidate.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className={`p-4 rounded-2xl border-2 transition-all cursor-pointer ${
                    selectedIds.has(candidate.id)
                      ? "border-primary bg-primary/5"
                      : "border-gray-100 hover:border-gray-200 bg-white"
                  }`}
                  onClick={() => handleToggle(candidate.id)}
                >
                  <div className="flex items-start gap-4">
                    {/* Checkbox */}
                    <div
                      className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center shrink-0 transition-colors ${
                        selectedIds.has(candidate.id)
                          ? "bg-primary border-primary text-white"
                          : "border-gray-300"
                      }`}
                    >
                      {selectedIds.has(candidate.id) && <Check size={14} />}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {editingId === candidate.id ? (
                        <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="text"
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            className="flex-1 px-3 py-2 rounded-lg border-2 border-primary focus:outline-none text-lg"
                            autoFocus
                          />
                          <button
                            onClick={handleSaveEdit}
                            className="px-4 py-2 bg-primary text-white rounded-lg font-medium"
                          >
                            완료
                          </button>
                        </div>
                      ) : (
                        <p className="text-lg font-medium text-gray-800 break-keep">
                          {editedTexts.has(candidate.id) ? (
                            <span>{getDisplayText(candidate)} <span className="text-xs text-blue-500 ml-1">(수정됨)</span></span>
                          ) : (
                            <HighlightedText text={candidate.text} matchedWords={candidate.matchedWords} />
                          )}
                        </p>
                      )}

                      {/* Metadata row */}
                      <div className="flex items-center gap-3 mt-2">
                        {/* Score */}
                        <span className="text-sm font-bold text-primary">
                          {Math.round(candidate.score)}점
                        </span>

                        {/* Difficulty */}
                        {candidate.difficulty && difficultyLabels[candidate.difficulty] && (
                          <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${difficultyColors[candidate.difficulty]}`}>
                            {difficultyLabels[candidate.difficulty]}
                          </span>
                        )}

                        {/* Word count */}
                        <span className="text-xs text-gray-500">
                          {editedTexts.has(candidate.id)
                            ? getDisplayText(candidate).split(/\s+/).length
                            : candidate.wordCount}어절
                        </span>

                        {/* Match count */}
                        {candidate.matchedWords.length > 0 && !editedTexts.has(candidate.id) && (
                          <span className="text-xs text-gray-500">
                            {candidate.matchedWords.length}매칭
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Edit button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartEdit(candidate);
                      }}
                      className="p-2 text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors shrink-0"
                    >
                      <Edit2 size={16} />
                    </button>
                  </div>
                </motion.div>
              ))}

              {filteredCandidates.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  {searchQuery ? "검색 결과가 없습니다" : "생성된 문장이 없습니다"}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 bg-gray-50 border-t border-gray-100 flex items-center justify-between shrink-0">
              <div className="text-sm text-gray-600">
                <span className="font-bold text-primary">{selectedCount}개</span> 선택됨
                {selectedCount < requestedCount && (
                  <span className="text-gray-400 ml-2">
                    (요청: {requestedCount}개)
                  </span>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="px-6 py-3 rounded-xl font-bold text-gray-500 hover:bg-gray-100 transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={selectedCount === 0}
                  className="px-8 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-primary to-secondary shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {selectedCount}개 추가하기
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
