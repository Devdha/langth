"use client";

import { motion } from "framer-motion";
import { MoreVertical, Copy, Trash2, Clock, FileText } from "lucide-react";
import { useState } from "react";
import { TherapySession, SessionColor } from "@/types/v2";

interface SessionCardProps {
  session: TherapySession;
  isActive: boolean;
  onSelect: (session: TherapySession) => void;
  onDuplicate: (id: string) => void;
  onDelete: (id: string) => void;
}

const colorMap: Record<SessionColor, string> = {
  purple: "bg-purple-500",
  pink: "bg-pink-500",
  blue: "bg-blue-500",
  green: "bg-emerald-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
};

function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "방금 전";
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  if (diffDays < 7) return `${diffDays}일 전`;
  return date.toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
}

export default function SessionCard({
  session,
  isActive,
  onSelect,
  onDuplicate,
  onDelete,
}: SessionCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const color = session.metadata.color || "purple";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      onClick={() => onSelect(session)}
      className={`relative p-4 rounded-xl cursor-pointer transition-all group ${
        isActive
          ? "bg-white shadow-lg ring-2 ring-purple-500"
          : "bg-white/50 hover:bg-white hover:shadow-md"
      }`}
    >
      {/* Color indicator */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${colorMap[color]}`}
      />

      {/* Menu button */}
      <div className="absolute top-2 right-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-gray-100 transition-all"
        >
          <MoreVertical size={16} className="text-gray-400" />
        </button>

        {/* Dropdown menu */}
        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(false);
              }}
            />
            <div className="absolute right-0 top-8 bg-white rounded-lg shadow-xl border border-gray-100 py-1 z-20 min-w-[120px]">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDuplicate(session.id);
                  setShowMenu(false);
                }}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <Copy size={14} />
                복제
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("이 세션을 삭제하시겠습니까?")) {
                    onDelete(session.id);
                  }
                  setShowMenu(false);
                }}
                className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <Trash2 size={14} />
                삭제
              </button>
            </div>
          </>
        )}
      </div>

      {/* Content */}
      <div className="pl-3">
        <h3 className="font-bold text-gray-800 truncate pr-8">{session.name}</h3>
        {session.metadata.patientName && (
          <p className="text-xs text-gray-500 mt-0.5">
            {session.metadata.patientName}
          </p>
        )}
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {formatDate(session.updatedAt)}
          </span>
          <span className="flex items-center gap-1">
            <FileText size={12} />
            {session.items.length}개
          </span>
        </div>
      </div>
    </motion.div>
  );
}
