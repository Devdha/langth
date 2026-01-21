"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import SettingsPanelV2 from "@/components/v2/SettingsPanelV2";
import SentenceListV2 from "@/components/v2/SentenceListV2";
import { useGenerateV2 } from "@/hooks/useGenerateV2";
import {
  GameSettingsV2,
  TherapyItemV2,
} from "@/types/v2";

const STORAGE_KEY_V2 = 'talk-talk-vending-v2-items';
const SETTINGS_KEY_V2 = 'talk-talk-vending-v2-settings';

const DEFAULT_SETTINGS: GameSettingsV2 = {
  language: 'ko',
  age: 4,
  count: 10,
  target: {
    phoneme: 'ㄹ',
    position: 'onset',
    minOccurrences: 1
  },
  sentenceLength: 3,
  diagnosis: 'SSD',
  therapyApproach: 'minimal_pairs',
  theme: '',
  communicativeFunction: null,
};

export default function V2Page() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  // Use lazy initialization to avoid hydration issues
  const [localItems, setLocalItems] = useState<TherapyItemV2[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const saved = localStorage.getItem(STORAGE_KEY_V2);
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [isInitialized, setIsInitialized] = useState(() => typeof window !== 'undefined');
  const [settings, setSettings] = useState<GameSettingsV2>(() => {
    if (typeof window === 'undefined') return DEFAULT_SETTINGS;
    try {
      const saved = localStorage.getItem(SETTINGS_KEY_V2);
      return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
    } catch { return DEFAULT_SETTINGS; }
  });
  const [isOnline, setIsOnline] = useState(() =>
    typeof window !== 'undefined' ? navigator.onLine : true
  );

  // Use the custom hook for API calls
  // Memoized callback to avoid recreating generate function on every render
  const handleGenerateSuccess = useCallback((items: TherapyItemV2[]) => {
    setLocalItems(items);
  }, []);

  const {
    generate,
    cancel: cancelGenerate,
    loading,
    error,
    warning,
    meta,
    clearWarning,
  } = useGenerateV2(handleGenerateSuccess);

  // Online/offline detection (subscribe to events only)
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Save items to localStorage
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(localItems));
    }
  }, [localItems, isInitialized]);

  // Save settings to localStorage
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(SETTINGS_KEY_V2, JSON.stringify(settings));
    }
  }, [settings, isInitialized]);

  const handleReset = () => {
    if (confirm('모든 문장을 삭제하시겠습니까?')) {
      setLocalItems([]);
    }
  };

  const handleGenerate = async (newSettings: GameSettingsV2) => {
    // Update settings state
    setSettings(newSettings);

    // Call the hook's generate function
    await generate(newSettings);
  };

  const handleDelete = (id: string) => {
    setLocalItems(localItems.filter(item => item.id !== id));
  };

  // TODO: Implement handleEdit with V2-specific edit modal
  const handleEdit = (item: TherapyItemV2) => {
    console.log('Edit not yet implemented', item);
  };

  // TODO: Implement handlePlay with speech synthesis
  const handlePlay = (item: TherapyItemV2) => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(item.text);
      utterance.lang = settings.language === 'en' ? 'en-US' : 'ko-KR';
      window.speechSynthesis.speak(utterance);
    } else {
      alert('이 브라우저에서는 음성 재생을 지원하지 않습니다.');
    }
  };

  return (
    <main className="min-h-screen bg-background text-foreground pb-20">
      <Header
        currentMode="list"
        onModeChange={() => {}}
        onNewGame={() => setIsSettingsOpen(true)}
        isV2={true}
      />

      {/* V2 Beta Badge */}
      <div className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-center py-3 px-4 font-bold shadow-lg">
        <span className="text-xl">🚀</span> V2 Beta - Enhanced Therapy Sentence Generator
      </div>

      {/* Offline banner */}
      {!isOnline && (
        <div className="bg-yellow-500 text-white text-center py-2 px-4 font-bold">
          ⚠️ 인터넷 연결이 끊어졌습니다. 연결 후 다시 시도해주세요.
        </div>
      )}

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Warning message */}
        {warning && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-700 font-medium flex items-center justify-between"
          >
            <span>⚠️ {warning}</span>
            <button
              onClick={clearWarning}
              className="text-yellow-500 hover:text-yellow-700 font-bold"
            >
              ✕
            </button>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loader"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-xl font-bold text-gray-500 animate-pulse mb-4">
                문장을 만들고 있어요...
              </p>
              <button
                onClick={cancelGenerate}
                className="px-4 py-2 text-sm font-bold text-gray-500 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                취소
              </button>
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="text-6xl mb-4">😢</div>
              <p className="text-xl font-bold text-red-500 mb-4">{error}</p>
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary/90 transition-colors"
              >
                다시 시도하기
              </button>
            </motion.div>
          ) : localItems.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-xl font-bold text-gray-500 mb-4">
                새로운 연습 문장을 만들어보세요
              </p>
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary/90 transition-colors"
              >
                시작하기
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="list"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex justify-between items-center mb-6 px-2">
                <h2 className="text-2xl font-bold text-gray-700 flex items-center gap-2">
                  <span className="text-3xl">📋</span> 연습 목록
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 font-bold bg-white px-3 py-1 rounded-lg border border-gray-100 shadow-sm">
                    총 {localItems.length}개
                  </span>
                  {localItems.length > 0 && (
                    <button
                      onClick={handleReset}
                      className="px-3 py-1 text-sm font-bold text-red-500 bg-red-50 rounded-lg border border-red-100 hover:bg-red-100 transition-colors"
                    >
                      초기화
                    </button>
                  )}
                </div>
              </div>
              <SentenceListV2
                items={localItems}
                onDelete={handleDelete}
                onEdit={handleEdit}
                onPlay={handlePlay}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* V2 Settings Panel */}
      <SettingsPanelV2
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onGenerate={handleGenerate}
        initialSettings={settings}
      />
    </main>
  );
}
