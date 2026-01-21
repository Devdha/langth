"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import SettingsPanelV2 from "@/components/v2/SettingsPanelV2";
import {
  GameSettingsV2,
  TherapyItemV2,
  GenerateRequestV2,
  GenerateResponseV2,
  ErrorResponseV2
} from "@/types/v2";

const STORAGE_KEY_V2 = 'talk-talk-vending-v2-items';
const SETTINGS_KEY_V2 = 'talk-talk-vending-v2-settings';
const LOADING_TIMEOUT = 30000; // 30 seconds

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
  const [items, setItems] = useState<TherapyItemV2[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [settings, setSettings] = useState<GameSettingsV2>(DEFAULT_SETTINGS);
  const [isOnline, setIsOnline] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedItems = localStorage.getItem(STORAGE_KEY_V2);
      const savedSettings = localStorage.getItem(SETTINGS_KEY_V2);

      if (savedItems) {
        try {
          setItems(JSON.parse(savedItems));
        } catch (e) {
          console.error('Failed to parse saved items', e);
        }
      }

      if (savedSettings) {
        try {
          setSettings(JSON.parse(savedSettings));
        } catch (e) {
          console.error('Failed to parse saved settings', e);
        }
      }

      setIsInitialized(true);
    }
  }, []);

  // Online/offline detection
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsOnline(navigator.onLine);

      const handleOnline = () => setIsOnline(true);
      const handleOffline = () => setIsOnline(false);

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  // Save items to localStorage
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(items));
    }
  }, [items, isInitialized]);

  // Save settings to localStorage
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(SETTINGS_KEY_V2, JSON.stringify(settings));
    }
  }, [settings, isInitialized]);

  const handleReset = () => {
    if (confirm('모든 문장을 삭제하시겠습니까?')) {
      setItems([]);
      setError(null);
    }
  };

  // TODO: Wire this up to SettingsPanelV2 when it's created
  const handleGenerate = async (newSettings: GameSettingsV2) => {
    if (!isOnline) {
      setError('인터넷에 연결되어 있지 않습니다. 연결 후 다시 시도해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setWarning(null);
    setSettings(newSettings);

    // AbortController setup
    abortControllerRef.current = new AbortController();
    const timeoutId = setTimeout(() => {
      abortControllerRef.current?.abort();
    }, LOADING_TIMEOUT);

    try {
      // TODO: Create API route at /api/v2/generate
      const requestBody: GenerateRequestV2 = {
        language: newSettings.language,
        age: newSettings.age,
        count: newSettings.count,
        target: newSettings.target,
        sentenceLength: newSettings.sentenceLength,
        diagnosis: newSettings.diagnosis,
        therapyApproach: newSettings.therapyApproach,
        theme: newSettings.theme || undefined,
        communicativeFunction: newSettings.communicativeFunction || undefined,
      };

      const res = await fetch('/api/v2/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });

      clearTimeout(timeoutId);
      const data: GenerateResponseV2 | ErrorResponseV2 = await res.json();

      if (res.ok && data.success) {
        const responseData = data.data;
        setItems(responseData.items);

        // Show warning if fewer items generated than requested
        if (responseData.meta.generatedCount < newSettings.count) {
          setWarning(
            `요청한 ${newSettings.count}개 중 ${responseData.meta.generatedCount}개만 생성되었습니다. 조건에 맞는 문장이 부족할 수 있습니다.`
          );
        }
      } else if (!data.success) {
        setError(data.error.message || '문장 생성에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof Error && err.name === 'AbortError') {
        setError('요청 시간이 초과되었습니다. 다시 시도해주세요.');
      } else {
        console.error("Failed to generate", err);
        setError('서버 연결에 실패했습니다. 다시 시도해주세요.');
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancelGenerate = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleDelete = (id: string) => {
    setItems(items.filter(item => item.id !== id));
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
              onClick={() => setWarning(null)}
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
                onClick={handleCancelGenerate}
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
          ) : items.length === 0 ? (
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
                    총 {items.length}개
                  </span>
                  {items.length > 0 && (
                    <button
                      onClick={handleReset}
                      className="px-3 py-1 text-sm font-bold text-red-500 bg-red-50 rounded-lg border border-red-100 hover:bg-red-100 transition-colors"
                    >
                      초기화
                    </button>
                  )}
                </div>
              </div>
              {/* TODO: Create V2-specific SentenceList component with highlighting */}
              <div className="space-y-4">
                {items.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-white p-4 rounded-xl shadow-sm border border-gray-100"
                  >
                    <p className="text-lg font-medium text-gray-800">{item.text}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                      <span>어절: {item.wordCount}</span>
                      <span>•</span>
                      <span>점수: {item.score.toFixed(2)}</span>
                      <span>•</span>
                      <span>매칭: {item.matchedWords.length}개</span>
                    </div>
                    <div className="mt-2 flex gap-2">
                      <button
                        onClick={() => handlePlay(item)}
                        className="px-3 py-1 text-xs font-bold text-blue-500 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                      >
                        듣기
                      </button>
                      <button
                        onClick={() => handleEdit(item)}
                        className="px-3 py-1 text-xs font-bold text-gray-500 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-3 py-1 text-xs font-bold text-red-500 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                      >
                        삭제
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
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
