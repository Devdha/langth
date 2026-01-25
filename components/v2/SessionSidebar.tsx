"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  FolderOpen,
} from "lucide-react";
import { TherapySession } from "@/types/v2";
import SessionCard from "./SessionCard";

interface SessionSidebarProps {
  sessions: TherapySession[];
  currentSessionId: string | null;
  onSelectSession: (session: TherapySession) => void;
  onNewSession: () => void;
  onDuplicateSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function SessionSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDuplicateSession,
  onDeleteSession,
  isCollapsed,
  onToggleCollapse,
}: SessionSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) {
      return sessions;
    }
    const query = searchQuery.toLowerCase();
    return sessions.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.metadata.patientName?.toLowerCase().includes(query)
    );
  }, [searchQuery, sessions]);

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 64 : 320 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="h-full bg-gradient-to-b from-purple-50 to-pink-50 border-r border-purple-100 flex flex-col relative"
    >
      {/* Toggle button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-6 z-10 w-6 h-6 bg-white rounded-full shadow-md border border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
      >
        {isCollapsed ? (
          <ChevronRight size={14} className="text-gray-600" />
        ) : (
          <ChevronLeft size={14} className="text-gray-600" />
        )}
      </button>

      {/* Header */}
      <div className="p-4 border-b border-purple-100">
        <AnimatePresence mode="wait">
          {!isCollapsed ? (
            <motion.div
              key="expanded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-gray-800 flex items-center gap-2">
                  <FolderOpen size={20} className="text-purple-500" />
                  세션 목록
                </h2>
                <span className="text-xs text-gray-400 bg-white px-2 py-1 rounded-full">
                  {sessions.length}개
                </span>
              </div>

              {/* Search */}
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  type="text"
                  placeholder="세션 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-white rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-center"
            >
              <FolderOpen size={24} className="text-purple-500" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* New Session Button */}
      <div className="p-4">
        <button
          onClick={onNewSession}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold transition-all ${
            isCollapsed
              ? "bg-purple-500 text-white p-3"
              : "bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/25"
          }`}
        >
          <Plus size={20} />
          {!isCollapsed && "새 세션"}
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-4 pt-0 space-y-2">
        <AnimatePresence>
          {!isCollapsed &&
            filteredSessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                isActive={session.id === currentSessionId}
                onSelect={onSelectSession}
                onDuplicate={onDuplicateSession}
                onDelete={onDeleteSession}
              />
            ))}
        </AnimatePresence>

        {!isCollapsed && filteredSessions.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            {searchQuery ? (
              <p className="text-sm">검색 결과가 없습니다</p>
            ) : (
              <>
                <FolderOpen size={48} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">세션이 없습니다</p>
                <p className="text-xs mt-1">새 세션을 만들어보세요</p>
              </>
            )}
          </div>
        )}
      </div>
    </motion.aside>
  );
}
