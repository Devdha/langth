"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Save,
  Check,
  Copy,
  Trash2,
  Edit3,
  Settings,
  User,
  Target,
} from "lucide-react";
import { TherapySession, SessionColor } from "@/types/v2";

interface SessionHeaderProps {
  session: TherapySession;
  hasUnsavedChanges: boolean;
  onSave: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onRename: (newName: string) => void;
  onOpenSettings: () => void;
}

const colorMap: Record<SessionColor, string> = {
  purple: "from-purple-500 to-purple-600",
  pink: "from-pink-500 to-pink-600",
  blue: "from-blue-500 to-blue-600",
  green: "from-emerald-500 to-emerald-600",
  orange: "from-orange-500 to-orange-600",
  red: "from-red-500 to-red-600",
};

export default function SessionHeader({
  session,
  hasUnsavedChanges,
  onSave,
  onDuplicate,
  onDelete,
  onRename,
  onOpenSettings,
}: SessionHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(session.name);
  const [isSaving, setIsSaving] = useState(false);
  const color = session.metadata.color || "purple";

  const handleSave = async () => {
    setIsSaving(true);
    await onSave();
    setTimeout(() => setIsSaving(false), 1000);
  };

  const handleRename = () => {
    if (editedName.trim() && editedName !== session.name) {
      onRename(editedName.trim());
    }
    setIsEditing(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-gradient-to-r ${colorMap[color]} rounded-2xl p-6 text-white shadow-lg`}
    >
      <div className="flex items-start justify-between">
        {/* Left: Session Info */}
        <div className="flex-1">
          {/* Session Name */}
          {isEditing ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRename();
                  if (e.key === "Escape") {
                    setEditedName(session.name);
                    setIsEditing(false);
                  }
                }}
                onBlur={handleRename}
                autoFocus
                className="text-2xl font-bold bg-white/20 rounded-lg px-3 py-1 text-white placeholder-white/50 outline-none focus:ring-2 focus:ring-white/50"
              />
            </div>
          ) : (
            <h1
              onClick={() => setIsEditing(true)}
              className="text-2xl font-bold cursor-pointer hover:bg-white/10 rounded-lg px-2 py-1 -mx-2 transition-colors flex items-center gap-2 group"
            >
              {session.name}
              <Edit3
                size={16}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </h1>
          )}

          {/* Meta Info */}
          <div className="flex items-center gap-4 mt-3 text-white/80 text-sm">
            {session.metadata.patientName && (
              <span className="flex items-center gap-1.5 bg-white/10 px-3 py-1 rounded-full">
                <User size={14} />
                {session.metadata.patientName}
              </span>
            )}
            <span className="flex items-center gap-1.5 bg-white/10 px-3 py-1 rounded-full">
              <Target size={14} />
              {session.settings.target.phoneme} ({session.settings.target.position})
            </span>
            <span className="bg-white/10 px-3 py-1 rounded-full">
              {session.items.length}개 문장
            </span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Save Status */}
          {hasUnsavedChanges ? (
            <span className="text-xs bg-yellow-400/20 text-yellow-100 px-3 py-1 rounded-full mr-2">
              수정됨
            </span>
          ) : (
            <span className="text-xs bg-white/20 text-white/80 px-3 py-1 rounded-full mr-2 flex items-center gap-1">
              <Check size={12} />
              저장됨
            </span>
          )}

          {/* Action Buttons */}
          <button
            onClick={handleSave}
            disabled={isSaving || !hasUnsavedChanges}
            className="p-2.5 bg-white/20 rounded-xl hover:bg-white/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="저장"
          >
            {isSaving ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Save size={18} />
              </motion.div>
            ) : (
              <Save size={18} />
            )}
          </button>

          <button
            onClick={onOpenSettings}
            className="p-2.5 bg-white/20 rounded-xl hover:bg-white/30 transition-colors"
            title="설정"
          >
            <Settings size={18} />
          </button>

          <button
            onClick={onDuplicate}
            className="p-2.5 bg-white/20 rounded-xl hover:bg-white/30 transition-colors"
            title="복제"
          >
            <Copy size={18} />
          </button>

          <button
            onClick={() => {
              if (confirm("이 세션을 삭제하시겠습니까?")) {
                onDelete();
              }
            }}
            className="p-2.5 bg-white/20 rounded-xl hover:bg-red-500/50 transition-colors"
            title="삭제"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
