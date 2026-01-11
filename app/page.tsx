"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import SettingsPanel from "@/components/SettingsPanel";
import SentenceList from "@/components/SentenceList";
import Roulette from "@/components/Roulette";
import EditModal from "@/components/EditModal";
import { GameMode, GameSettings, TherapyItem } from "@/types";

const STORAGE_KEY = 'talk-talk-vending-items';
const SETTINGS_KEY = 'talk-talk-vending-settings';
const LOADING_TIMEOUT = 30000; // 30초

export default function Home() {
  const [mode, setMode] = useState<GameMode>('list');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [items, setItems] = useState<TherapyItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [editingItem, setEditingItem] = useState<TherapyItem | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const [settings, setSettings] = useState<GameSettings>({
    phoneme: '',
    level: 3,
    theme: '',
    count: 10,
    language: 'ko',
    age: 4
  });

  const [error, setError] = useState<string | null>(null);

  // localStorage에서 데이터 로드
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedItems = localStorage.getItem(STORAGE_KEY);
      const savedSettings = localStorage.getItem(SETTINGS_KEY);

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

  // 온라인/오프라인 감지
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

  // items 변경 시 localStorage에 저장
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    }
  }, [items, isInitialized]);

  // settings 변경 시 localStorage에 저장
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    }
  }, [settings, isInitialized]);

  // 초기화 함수
  const handleReset = () => {
    if (confirm('모든 문장을 삭제하시겠습니까?')) {
      setItems([]);
      setError(null);
    }
  };

  const handleGenerate = async (newSettings: GameSettings) => {
    if (!isOnline) {
      setError('인터넷에 연결되어 있지 않습니다. 연결 후 다시 시도해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setWarning(null);
    setSettings(newSettings);

    // AbortController 설정
    abortControllerRef.current = new AbortController();
    const timeoutId = setTimeout(() => {
      abortControllerRef.current?.abort();
    }, LOADING_TIMEOUT);

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: newSettings }),
        signal: abortControllerRef.current.signal,
      });

      clearTimeout(timeoutId);
      const data = await res.json();

      if (res.ok && data.success && data.items && data.items.length > 0) {
        setItems(data.items);
        setMode('list');

        // 부족한 결과 안내
        if (data.items.length < newSettings.count) {
          setWarning(`요청한 ${newSettings.count}개 중 ${data.items.length}개만 생성되었습니다. 조건에 맞는 문장이 부족할 수 있습니다.`);
        }
      } else {
        setError(data.error || '문장 생성에 실패했습니다. 다시 시도해주세요.');
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

  const handleEdit = (item: TherapyItem) => {
    setEditingItem(item);
  };

  const handleEditSave = (newText: string) => {
    if (editingItem) {
      setItems(items.map(i => i.id === editingItem.id ? { ...i, text: newText } : i));
    }
  };

  const handlePlay = (item: TherapyItem) => {
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
        currentMode={mode} 
        onModeChange={setMode} 
        onNewGame={() => setIsSettingsOpen(true)} 
      />

      {/* 오프라인 배너 */}
      {!isOnline && (
        <div className="bg-yellow-500 text-white text-center py-2 px-4 font-bold">
          ⚠️ 인터넷 연결이 끊어졌습니다. 연결 후 다시 시도해주세요.
        </div>
      )}

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 경고 메시지 */}
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
          ) : mode === 'list' ? (
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
              <SentenceList 
                items={items} 
                onDelete={handleDelete} 
                onEdit={handleEdit}
                onPlay={handlePlay}
              />
            </motion.div>
          ) : (
            <motion.div
              key="roulette"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
               <div className="flex justify-center items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-700 flex items-center gap-2 bg-white px-6 py-2 rounded-full shadow-sm border border-gray-100">
                  <span className="text-3xl">🎡</span> 룰렛 돌리기
                </h2>
              </div>
              <Roulette items={items} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onGenerate={handleGenerate}
        initialSettings={settings}
      />

      <EditModal
        isOpen={!!editingItem}
        initialText={editingItem?.text || ''}
        onClose={() => setEditingItem(null)}
        onSave={handleEditSave}
      />
    </main>
  );
}
