"use client";

import { motion } from "framer-motion";
import { List, Disc, Plus } from "lucide-react";
import { GameMode } from "@/types";

interface HeaderProps {
  currentMode: GameMode;
  onModeChange: (mode: GameMode) => void;
  onNewGame: () => void;
}

export default function Header({ currentMode, onModeChange, onNewGame }: HeaderProps) {
  return (
    <header className="w-full bg-white/50 backdrop-blur-md border-b-4 border-primary/20 p-3 md:p-4 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:justify-between md:items-center gap-3">
        {/* Row 1: Logo + New Button */}
        <div className="flex justify-between items-center">
          <motion.button
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={() => onModeChange('list')}
            className="flex items-center gap-2 md:gap-3 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="w-10 h-10 md:w-12 md:h-12 bg-primary rounded-xl md:rounded-2xl flex items-center justify-center shadow-lg transform -rotate-6">
              <span className="text-xl md:text-2xl">🗣️</span>
            </div>
            <h1 className="text-xl md:text-3xl font-bold text-primary tracking-tight text-outline font-display whitespace-nowrap">
              말놀이 자판기
            </h1>
          </motion.button>

          {/* New Button - visible on mobile in row 1 */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNewGame}
            className="md:hidden flex items-center gap-1 bg-primary text-white px-3 py-2 rounded-xl font-bold shadow-lg hover:shadow-xl hover:bg-primary/90 transition-all border-b-2 border-orange-600 active:border-b-0 active:translate-y-0.5 text-sm"
          >
            <Plus size={18} strokeWidth={3} />
            <span>새로 만들기</span>
          </motion.button>
        </div>

        {/* Row 2: Mode Toggle (mobile) / All controls (desktop) */}
        <div className="flex items-center justify-center md:justify-end gap-2 md:gap-4">
          <div className="flex bg-white rounded-xl p-1 shadow-sm border border-gray-100 flex-1 md:flex-none max-w-xs md:max-w-none">
            <button
              onClick={() => onModeChange('list')}
              className={`flex items-center justify-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 rounded-lg font-bold transition-all flex-1 md:flex-none text-sm md:text-base ${
                currentMode === 'list'
                  ? 'bg-secondary text-white shadow-md'
                  : 'text-gray-400 hover:text-secondary hover:bg-secondary/10'
              }`}
            >
              <List size={18} className="md:w-5 md:h-5" />
              <span>목록</span>
            </button>
            <button
              onClick={() => onModeChange('roulette')}
              className={`flex items-center justify-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 rounded-lg font-bold transition-all flex-1 md:flex-none text-sm md:text-base ${
                currentMode === 'roulette'
                  ? 'bg-accent text-white shadow-md'
                  : 'text-gray-400 hover:text-accent hover:bg-accent/10'
              }`}
            >
              <Disc size={18} className="md:w-5 md:h-5" />
              <span>룰렛</span>
            </button>
          </div>

          {/* New Button - desktop only */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNewGame}
            className="hidden md:flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-xl font-bold shadow-lg hover:shadow-xl hover:bg-primary/90 transition-all border-b-4 border-orange-600 active:border-b-0 active:translate-y-1"
          >
            <Plus size={24} strokeWidth={3} />
            <span>새로 만들기</span>
          </motion.button>
        </div>
      </div>
    </header>
  );
}
