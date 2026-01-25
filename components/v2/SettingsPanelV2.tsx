"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronDown, Check } from "lucide-react";
import { GameSettingsV2, LanguageV2, CommunicativeFunction, DiagnosisType, TherapyApproach } from "@/types/v2";
import PhonemeSelector from "./PhonemeSelector";

interface SettingsPanelV2Props {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (settings: GameSettingsV2) => void;
  initialSettings?: GameSettingsV2;
}

const LANGUAGES = [
  { id: 'ko' as const, label: '한국어', icon: '🇰🇷' },
  { id: 'en' as const, label: 'English', icon: '🇺🇸' },
];

// Note: minimal_pairs and maximal_oppositions are planned for a separate word-pair discrimination mode
const THERAPY_APPROACHES = [
  {
    id: 'complexity' as const,
    label: '복잡성 접근',
    desc: '목표 음소가 포함된 문장 생성 (난이도별)',
    category: 'SSD 치료',
    defaultDiagnosis: 'SSD' as const,
  },
  {
    id: 'core_vocabulary' as const,
    label: '핵심어휘',
    desc: '고빈도 기능어 중심 문장',
    category: 'ASD/LD 치료',
    defaultDiagnosis: 'ASD' as const,
  },
];

const AGES = [
  { id: 3, label: '만 3세' },
  { id: 4, label: '만 4세' },
  { id: 5, label: '만 5세' },
  { id: 6, label: '만 6세' },
  { id: 7, label: '만 7세' },
];

const COUNTS = [3, 5, 10, 15, 20];

export default function SettingsPanelV2({
  isOpen,
  onClose,
  onGenerate,
  initialSettings
}: SettingsPanelV2Props) {
  // Form state
  const [language, setLanguage] = useState<LanguageV2>(initialSettings?.language || 'ko');
  const [therapyApproach, setTherapyApproach] = useState<TherapyApproach>(initialSettings?.therapyApproach || 'complexity');
  const [diagnosis, setDiagnosis] = useState<DiagnosisType>(initialSettings?.diagnosis || 'SSD');
  const [phoneme, setPhoneme] = useState(initialSettings?.target?.phoneme || 'ㄹ');
  const [position, setPosition] = useState(initialSettings?.target?.position || 'onset');
  const [minOccurrences, setMinOccurrences] = useState(initialSettings?.target?.minOccurrences || 1);
  const [sentenceLength, setSentenceLength] = useState(initialSettings?.sentenceLength || 3);
  const [age, setAge] = useState<3 | 4 | 5 | 6 | 7>(initialSettings?.age || 4);
  const [count, setCount] = useState(initialSettings?.count || 10);

  // Step tracking - which steps are "confirmed"
  const [confirmedSteps, setConfirmedSteps] = useState<Set<number>>(new Set());

  // Current visible step (auto-expands next unconfirmed step)
  const [expandedStep, setExpandedStep] = useState(1);

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setConfirmedSteps(new Set());
      setExpandedStep(1);
    }
  }, [isOpen]);

  const confirmStep = (step: number) => {
    setConfirmedSteps(prev => new Set([...prev, step]));
    // Auto-expand next step
    if (step < 5) {
      setExpandedStep(step + 1);
    }
  };

  const handleLanguageSelect = (lang: LanguageV2) => {
    setLanguage(lang);
    // Reset phoneme when language changes
    setPhoneme(lang === 'ko' ? 'ㄹ' : 'R');
    confirmStep(1);
  };

  const handleApproachSelect = (approach: TherapyApproach) => {
    setTherapyApproach(approach);
    const config = THERAPY_APPROACHES.find(a => a.id === approach);
    if (config) {
      setDiagnosis(config.defaultDiagnosis);
    }
    confirmStep(2);
    // 핵심어휘는 음소 선택이 필요 없으므로 Step 3도 자동 확인
    if (approach === 'core_vocabulary') {
      confirmStep(3);
    }
  };

  const handlePhonemeConfirm = () => {
    confirmStep(3);
  };

  const handleDetailsConfirm = () => {
    confirmStep(4);
  };

  const handleGenerate = () => {
    const settings: GameSettingsV2 = {
      language,
      age,
      count,
      ...(therapyApproach !== 'core_vocabulary'
        ? {
            target: {
              phoneme,
              position,
              minOccurrences,
            },
          }
        : {}),
      sentenceLength,
      diagnosis,
      therapyApproach,
      theme: '',
      communicativeFunction: null,
    };
    onGenerate(settings);
    onClose();
  };

  const isStepVisible = (step: number) => {
    if (step === 1) return true;
    return confirmedSteps.has(step - 1);
  };

  const isStepConfirmed = (step: number) => confirmedSteps.has(step);

  const StepHeader = ({ step, title, isExpanded, onToggle, confirmed }: {
    step: number;
    title: string;
    isExpanded: boolean;
    onToggle: () => void;
    confirmed: boolean;
  }) => (
    <button
      onClick={onToggle}
      className={`w-full flex items-center gap-3 p-4 rounded-2xl transition-all ${
        confirmed
          ? 'bg-green-50 border-2 border-green-200'
          : isExpanded
            ? 'bg-purple-50 border-2 border-purple-300'
            : 'bg-gray-50 border-2 border-gray-100 hover:border-gray-200'
      }`}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
        confirmed
          ? 'bg-green-500 text-white'
          : isExpanded
            ? 'bg-purple-500 text-white'
            : 'bg-gray-300 text-white'
      }`}>
        {confirmed ? <Check size={16} /> : step}
      </div>
      <span className={`flex-1 text-left font-bold ${confirmed ? 'text-green-700' : 'text-gray-700'}`}>
        {title}
      </span>
      <ChevronDown
        size={20}
        className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
      />
    </button>
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-5 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                ✨ 문장 만들기
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-full transition-colors"
              >
                <X size={20} className="text-white" />
              </button>
            </div>

            {/* Steps */}
            <div className="p-6 space-y-4 max-h-[65vh] overflow-y-auto">

              {/* Step 1: Language */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <StepHeader
                  step={1}
                  title={isStepConfirmed(1) ? `언어: ${language === 'ko' ? '한국어 🇰🇷' : 'English 🇺🇸'}` : '언어 선택'}
                  isExpanded={expandedStep === 1}
                  onToggle={() => setExpandedStep(expandedStep === 1 ? 0 : 1)}
                  confirmed={isStepConfirmed(1)}
                />
                <AnimatePresence>
                  {expandedStep === 1 && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-4 flex gap-3 justify-center">
                        {LANGUAGES.map((l) => (
                          <button
                            key={l.id}
                            onClick={() => handleLanguageSelect(l.id)}
                            className={`flex-1 py-4 rounded-2xl font-bold transition-all flex items-center justify-center gap-2 ${
                              language === l.id
                                ? 'bg-purple-500 text-white shadow-lg'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            <span className="text-2xl">{l.icon}</span>
                            <span>{l.label}</span>
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* Step 2: Therapy Approach */}
              {isStepVisible(2) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <StepHeader
                    step={2}
                    title={isStepConfirmed(2) ? `접근법: ${THERAPY_APPROACHES.find(a => a.id === therapyApproach)?.label}` : '치료 접근법'}
                    isExpanded={expandedStep === 2}
                    onToggle={() => setExpandedStep(expandedStep === 2 ? 0 : 2)}
                    confirmed={isStepConfirmed(2)}
                  />
                  <AnimatePresence>
                    {expandedStep === 2 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 space-y-2">
                          {THERAPY_APPROACHES.map((a) => (
                            <button
                              key={a.id}
                              onClick={() => handleApproachSelect(a.id)}
                              className={`w-full p-3 rounded-xl border-2 transition-all text-left ${
                                therapyApproach === a.id
                                  ? 'border-purple-500 bg-purple-50'
                                  : 'border-gray-100 hover:border-gray-200 bg-white'
                              }`}
                            >
                              <div className="font-bold text-gray-800">{a.label}</div>
                              <div className="text-xs text-gray-500">{a.desc}</div>
                            </button>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* Step 3: Target Phoneme (only for non-core_vocabulary) */}
              {isStepVisible(3) && therapyApproach !== 'core_vocabulary' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <StepHeader
                    step={3}
                    title={isStepConfirmed(3) ? `목표 음소: ${phoneme}` : '목표 음소'}
                    isExpanded={expandedStep === 3}
                    onToggle={() => setExpandedStep(expandedStep === 3 ? 0 : 3)}
                    confirmed={isStepConfirmed(3)}
                  />
                  <AnimatePresence>
                    {expandedStep === 3 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 space-y-4">
                          <PhonemeSelector
                            language={language}
                            phoneme={phoneme}
                            position={position}
                            minOccurrences={minOccurrences}
                            onPhonemeChange={setPhoneme}
                            onPositionChange={setPosition}
                            onMinOccurrencesChange={setMinOccurrences}
                          />
                          <button
                            onClick={handlePhonemeConfirm}
                            className="w-full py-2 bg-purple-500 text-white rounded-xl font-bold hover:bg-purple-600 transition-colors"
                          >
                            다음
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* Step 4: Details (Length, Age, Count) - shows as step 3 for core_vocabulary */}
              {isStepVisible(4) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <StepHeader
                    step={therapyApproach === 'core_vocabulary' ? 3 : 4}
                    title={isStepConfirmed(4) ? `${sentenceLength}어절, ${age}세, ${count}개` : '세부 설정'}
                    isExpanded={expandedStep === 4}
                    onToggle={() => setExpandedStep(expandedStep === 4 ? 0 : 4)}
                    confirmed={isStepConfirmed(4)}
                  />
                  <AnimatePresence>
                    {expandedStep === 4 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 space-y-5">
                          {/* Sentence Length */}
                          <div>
                            <h4 className="text-sm font-bold text-gray-600 mb-2">문장 길이</h4>
                            <div className="flex gap-2 justify-center">
                              {[2, 3, 4, 5, 6].map((n) => (
                                <button
                                  key={n}
                                  onClick={() => setSentenceLength(n)}
                                  className={`w-12 h-12 rounded-full font-bold transition-all ${
                                    sentenceLength === n
                                      ? 'bg-teal-500 text-white shadow-lg'
                                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                  }`}
                                >
                                  {n}
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Age */}
                          <div>
                            <h4 className="text-sm font-bold text-gray-600 mb-2">대상 연령</h4>
                            <div className="flex gap-2 justify-center flex-wrap">
                              {AGES.map((a) => (
                                <button
                                  key={a.id}
                                  onClick={() => setAge(a.id as 3 | 4 | 5 | 6 | 7)}
                                  className={`px-3 py-2 rounded-xl font-bold transition-all ${
                                    age === a.id
                                      ? 'bg-orange-500 text-white shadow-lg'
                                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                  }`}
                                >
                                  {a.label}
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Count */}
                          <div>
                            <h4 className="text-sm font-bold text-gray-600 mb-2">생성 개수</h4>
                            <div className="flex gap-2 justify-center">
                              {COUNTS.map((c) => (
                                <button
                                  key={c}
                                  onClick={() => setCount(c)}
                                  className={`w-12 h-12 rounded-full font-bold transition-all ${
                                    count === c
                                      ? 'bg-pink-500 text-white shadow-lg'
                                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                  }`}
                                >
                                  {c}
                                </button>
                              ))}
                            </div>
                          </div>

                          <button
                            onClick={handleDetailsConfirm}
                            className="w-full py-2 bg-purple-500 text-white rounded-xl font-bold hover:bg-purple-600 transition-colors"
                          >
                            다음
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* Generate Button */}
              {isStepConfirmed(4) && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="pt-4"
                >
                  <button
                    onClick={handleGenerate}
                    className="w-full py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-all hover:scale-[1.02] active:scale-[0.98]"
                  >
                    ✨ 문장 생성하기
                  </button>
                </motion.div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
