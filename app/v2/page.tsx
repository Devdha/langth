"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import SettingsPanelV2 from "@/components/v2/SettingsPanelV2";
import SentenceListV2 from "@/components/v2/SentenceListV2";
import ContrastModeView from "@/components/v2/ContrastModeView";
import Roulette from "@/components/Roulette";
import SessionSidebar from "@/components/v2/SessionSidebar";
import SessionHeader from "@/components/v2/SessionHeader";
import NewSessionModal from "@/components/v2/NewSessionModal";
import CandidateSelectionModal from "@/components/v2/CandidateSelectionModal";
import EmptyState from "@/components/v2/EmptyState";
import EditModal from "@/components/EditModal";
import { useGenerateV2 } from "@/hooks/useGenerateV2";
import { GameMode } from "@/types";
import {
  GameSettingsV2,
  TherapyItemV2,
  TherapySession,
  SessionColor,
  ContrastSet,
} from "@/types/v2";
import {
  getAllSessions,
  createSession,
  updateSession,
  deleteSession,
  duplicateSession,
} from "@/lib/db/sessions";

const DEFAULT_SETTINGS: GameSettingsV2 = {
  language: "ko",
  age: 4,
  count: 10,
  target: {
    phoneme: "ㄹ",
    position: "onset",
    minOccurrences: 1,
  },
  sentenceLength: 3,
  diagnosis: "SSD",
  therapyApproach: "complexity",
  theme: "",
  communicativeFunction: null,
};

export default function V2Page() {
  // Session state
  const [sessions, setSessions] = useState<TherapySession[]>([]);
  const [currentSession, setCurrentSession] = useState<TherapySession | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [editingItem, setEditingItem] = useState<TherapyItemV2 | null>(null);

  // UI state
  const [currentMode, setCurrentMode] = useState<GameMode>("list");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settingsPanelKey, setSettingsPanelKey] = useState(0);
  const [isNewSessionModalOpen, setIsNewSessionModalOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isOnline, setIsOnline] = useState(() =>
    typeof window !== "undefined" ? navigator.onLine : true
  );

  // Candidate selection state
  const [isSelectionModalOpen, setIsSelectionModalOpen] = useState(false);
  const [pendingCandidates, setPendingCandidates] = useState<TherapyItemV2[]>([]);
  const [pendingContrastSets, setPendingContrastSets] = useState<ContrastSet[]>([]);
  const [pendingRequestedCount, setPendingRequestedCount] = useState(10);

  // Generate hook - show selection modal instead of directly adding
  const handleGenerateSuccess = useCallback((items: TherapyItemV2[], contrastSets: ContrastSet[]) => {
    if (currentSession) {
      setPendingCandidates(items);
      setPendingContrastSets(contrastSets);
      setPendingRequestedCount(currentSession.settings.count);
      setIsSelectionModalOpen(true);
      setIsSettingsOpen(false);
    }
  }, [currentSession]);

  const {
    generate,
    cancel: cancelGenerate,
    loading,
    error,
    warning,
    clearWarning,
  } = useGenerateV2(handleGenerateSuccess);

  // Load sessions on mount and restore last viewed session
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const loaded = await getAllSessions();
        setSessions(loaded);

        // Restore last viewed session from localStorage
        const lastSessionId = localStorage.getItem("v2_last_session_id");
        if (lastSessionId && loaded.length > 0) {
          const lastSession = loaded.find((s) => s.id === lastSessionId);
          if (lastSession) {
            setCurrentSession(lastSession);
          }
        }
      } catch (e) {
        console.error("Failed to load sessions", e);
      }
      setIsInitialized(true);
    };
    loadSessions();
  }, []);

  // Persist current session ID to localStorage
  useEffect(() => {
    if (currentSession) {
      localStorage.setItem("v2_last_session_id", currentSession.id);
    }
  }, [currentSession]);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Session handlers - defined before keyboard shortcuts effect
  const handleSaveSession = useCallback(async () => {
    if (!currentSession) return;
    await updateSession(currentSession.id, {
      items: currentSession.items,
      contrastSets: currentSession.contrastSets,
      settings: currentSession.settings,
      metadata: currentSession.metadata,
    });
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSession.id
          ? { ...currentSession, updatedAt: Date.now() }
          : s
      )
    );
    setHasUnsavedChanges(false);
  }, [currentSession]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + S to save
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        if (currentSession && hasUnsavedChanges) {
          handleSaveSession();
        }
      }
      // Escape to close modals/panels
      if (e.key === "Escape") {
        if (isSettingsOpen) {
          setIsSettingsOpen(false);
        } else if (isNewSessionModalOpen) {
          setIsNewSessionModalOpen(false);
        } else if (isMobileSidebarOpen) {
          setIsMobileSidebarOpen(false);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSession, hasUnsavedChanges, isSettingsOpen, isNewSessionModalOpen, isMobileSidebarOpen, handleSaveSession]);

  const handleCreateSession = async (
    name: string,
    patientName: string,
    color: SessionColor
  ) => {
    const session = await createSession(name, DEFAULT_SETTINGS, {
      patientName: patientName || undefined,
      color,
    });
    setSessions((prev) => [session, ...prev]);
    setCurrentSession(session);
    setIsNewSessionModalOpen(false);
    setSettingsPanelKey((prev) => prev + 1);
    setIsSettingsOpen(true); // Open settings for new session
  };

  const openSettingsPanel = () => {
    setSettingsPanelKey((prev) => prev + 1);
    setIsSettingsOpen(true);
  };

  const handleSelectSession = (session: TherapySession) => {
    if (hasUnsavedChanges && currentSession) {
      if (!confirm("저장하지 않은 변경사항이 있습니다. 계속하시겠습니까?")) {
        return;
      }
    }
    setCurrentSession(session);
    setHasUnsavedChanges(false);
    setIsMobileSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const handleDuplicateSession = async (id: string) => {
    const duplicated = await duplicateSession(id);
    if (duplicated) {
      setSessions((prev) => [duplicated, ...prev]);
    }
  };

  const handleDeleteSession = async (id: string) => {
    await deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (currentSession?.id === id) {
      setCurrentSession(null);
      setHasUnsavedChanges(false);
    }
  };

  const handleRenameSession = async (newName: string) => {
    if (!currentSession) return;
    const updated = await updateSession(currentSession.id, { name: newName });
    if (updated) {
      setCurrentSession(updated);
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSession.id ? updated : s))
      );
    }
  };

  const handleGenerate = async (newSettings: GameSettingsV2) => {
    if (!currentSession) return;
    setCurrentSession((prev) =>
      prev ? { ...prev, settings: newSettings } : null
    );
    setHasUnsavedChanges(true);
    await generate(newSettings);
  };

  const handleSelectionConfirm = (selected: TherapyItemV2[]) => {
    if (!currentSession) return;
    const sessionId = currentSession.id;
    const updatedItems = selected;
    const updatedContrastSets = pendingContrastSets;

    setCurrentSession((prev) =>
      prev ? { ...prev, items: updatedItems, contrastSets: updatedContrastSets } : null
    );
    setHasUnsavedChanges(false);
    setIsSelectionModalOpen(false);
    setPendingCandidates([]);
    setPendingContrastSets([]);

    void (async () => {
      const saved = await updateSession(sessionId, {
        items: updatedItems,
        contrastSets: updatedContrastSets,
      });
      if (saved) {
        setCurrentSession(saved);
        setSessions((prev) => prev.map((s) => (s.id === sessionId ? saved : s)));
        setHasUnsavedChanges(false);
      } else {
        setHasUnsavedChanges(true);
      }
    })();
  };

  const handleSelectionClose = () => {
    setIsSelectionModalOpen(false);
    setPendingCandidates([]);
    setPendingContrastSets([]);
  };

  const handleDelete = (id: string) => {
    if (!currentSession) return;
    setCurrentSession((prev) =>
      prev ? { ...prev, items: prev.items.filter((item) => item.id !== id) } : null
    );
    setHasUnsavedChanges(true);
  };

  const handleEdit = (item: TherapyItemV2) => {
    setEditingItem(item);
  };

  const handleEditSave = (newText: string) => {
    if (!editingItem) return;
    const trimmedText = newText.trim();
    const wordCount = trimmedText ? trimmedText.split(/\s+/).length : 0;
    setCurrentSession((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        items: prev.items.map((item) =>
          item.id === editingItem.id
            ? {
                ...item,
                text: trimmedText,
                wordCount,
                matchedWords: [],
                score: 0,
              }
            : item
        ),
      };
    });
    setHasUnsavedChanges(true);
  };

  const handlePlay = (item: TherapyItemV2) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(item.text);
      utterance.lang = currentSession?.settings.language === "en" ? "en-US" : "ko-KR";
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleReset = () => {
    if (!currentSession) return;
    if (confirm("모든 문장을 삭제하시겠습니까?")) {
      setCurrentSession((prev) => (prev ? { ...prev, items: [], contrastSets: [] } : null));
      setHasUnsavedChanges(true);
    }
  };

  // Note: contrastSets display is disabled - minimal_pairs/maximal_oppositions
  // are planned for a separate word-pair discrimination mode
  const showContrastSets = false;

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50/30 flex flex-col">
      <Header
        currentMode={currentMode}
        onModeChange={setCurrentMode}
        onNewGame={() => currentSession && openSettingsPanel()}
        isV2={true}
      />

      {/* Offline banner */}
      {!isOnline && (
        <div className="bg-yellow-500 text-white text-center py-2 px-4 font-bold">
          ⚠️ 인터넷 연결이 끊어졌습니다. 연결 후 다시 시도해주세요.
        </div>
      )}

      <div className="flex-1 flex overflow-hidden relative">
        {/* Mobile sidebar overlay */}
        <AnimatePresence>
          {isMobileSidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileSidebarOpen(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
            />
          )}
        </AnimatePresence>

        {/* Sidebar - hidden on mobile, visible on desktop */}
        <div className={`
          fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
          transform transition-transform duration-300 ease-in-out
          ${isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          lg:transform-none
        `}>
          <SessionSidebar
            sessions={sessions}
            currentSessionId={currentSession?.id || null}
            onSelectSession={handleSelectSession}
            onNewSession={() => {
              setIsNewSessionModalOpen(true);
              setIsMobileSidebarOpen(false);
            }}
            onDuplicateSession={handleDuplicateSession}
            onDeleteSession={handleDeleteSession}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setIsMobileSidebarOpen(true)}
          className="fixed bottom-6 left-6 z-30 lg:hidden w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-all"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
            <line x1="9" x2="9" y1="3" y2="21"/>
          </svg>
        </button>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-6 py-8">
            {currentSession ? (
              <>
                {/* Session Header */}
                <SessionHeader
                  session={currentSession}
                  hasUnsavedChanges={hasUnsavedChanges}
                  onSave={handleSaveSession}
                  onDuplicate={() => handleDuplicateSession(currentSession.id)}
                  onDelete={() => handleDeleteSession(currentSession.id)}
                  onRename={handleRenameSession}
                  onOpenSettings={() => openSettingsPanel()}
                />

                {/* Warning message */}
                {warning && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-700 font-medium flex items-center justify-between"
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

                {/* Content Area */}
                <div className="mt-6">
                  <AnimatePresence mode="wait">
                    {loading ? (
                      <motion.div
                        key="loader"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center justify-center py-20"
                      >
                        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4" />
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
                          onClick={() => openSettingsPanel()}
                          className="px-6 py-3 bg-purple-500 text-white rounded-xl font-bold hover:bg-purple-600 transition-colors"
                        >
                          다시 시도하기
                        </button>
                      </motion.div>
                    ) : currentSession.items.length === 0 && currentMode !== "contrast" ? (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center justify-center py-20"
                      >
                        <div className="text-6xl mb-4">🎯</div>
                        <p className="text-xl font-bold text-gray-500 mb-4">
                          문장을 생성해보세요
                        </p>
                        <button
                          onClick={() => openSettingsPanel()}
                          className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-bold hover:shadow-lg transition-all"
                        >
                          문장 생성하기
                        </button>
                      </motion.div>
                    ) : currentMode === "contrast" ? (
                      <motion.div
                        key="contrast"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <ContrastModeView language={currentSession.settings.language} />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="list"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <div className="flex justify-between items-center mb-6">
                          <h2 className="text-xl font-bold text-gray-700 flex items-center gap-2">
                            📋 {showContrastSets ? "생성된 대조 세트" : "생성된 문장"}
                            <span className="text-sm font-normal text-gray-400 bg-white px-2 py-1 rounded-lg">
                              {showContrastSets
                                ? currentSession.contrastSets?.length || 0
                                : currentSession.items.length}개
                            </span>
                          </h2>
                          <div className="flex gap-2">
                            <button
                              onClick={() => openSettingsPanel()}
                              className="px-4 py-2 text-sm font-bold text-purple-600 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
                            >
                              + 더 생성하기
                            </button>
                            <button
                              onClick={handleReset}
                              className="px-4 py-2 text-sm font-bold text-red-500 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                            >
                              초기화
                            </button>
                          </div>
                        </div>
                        {currentMode === "list" ? (
                          <SentenceListV2
                            items={currentSession.items}
                            contrastSets={currentSession.contrastSets}
                            therapyApproach={currentSession.settings.therapyApproach}
                            language={currentSession.settings.language}
                            onDelete={handleDelete}
                            onEdit={handleEdit}
                            onPlay={handlePlay}
                          />
                        ) : currentMode === "roulette" ? (
                          <Roulette items={currentSession.items} />
                        ) : null}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            ) : (
              <EmptyState
                onNewSession={() => setIsNewSessionModalOpen(true)}
                hasExistingSessions={sessions.length > 0}
              />
            )}
          </div>
        </main>
      </div>

      {/* Modals */}
      <NewSessionModal
        isOpen={isNewSessionModalOpen}
        onClose={() => setIsNewSessionModalOpen(false)}
        onCreate={handleCreateSession}
      />

      {currentSession && (
        <SettingsPanelV2
          key={`${currentSession.id}-${settingsPanelKey}`}
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          onGenerate={handleGenerate}
          initialSettings={currentSession.settings}
        />
      )}

      <EditModal
        isOpen={!!editingItem}
        initialText={editingItem?.text || ""}
        onClose={() => setEditingItem(null)}
        onSave={handleEditSave}
      />

      <CandidateSelectionModal
        isOpen={isSelectionModalOpen}
        candidates={pendingCandidates}
        requestedCount={pendingRequestedCount}
        onClose={handleSelectionClose}
        onConfirm={handleSelectionConfirm}
      />
    </div>
  );
}
