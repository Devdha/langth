"use client";

import { useState, useRef } from "react";
import { motion, useAnimation, AnimatePresence } from "framer-motion";
import { Volume2, RotateCcw, Sparkles } from "lucide-react";
import { TherapyItem } from "@/types";
import { TherapyItemV2 } from "@/types/v2";

// 룰렛에서 사용하는 최소한의 속성만 정의
type RouletteItem = Pick<TherapyItem, 'id' | 'text'> | Pick<TherapyItemV2, 'id' | 'text'>;

interface RouletteProps {
  items: RouletteItem[];
}

// V2 디자인 시스템에 맞는 색상 팔레트
const COLORS = [
  '#8B5CF6', // purple-500
  '#EC4899', // pink-500
  '#3B82F6', // blue-500
  '#10B981', // emerald-500
  '#F97316', // orange-500
  '#EF4444', // red-500
  '#06B6D4', // cyan-500
  '#84CC16', // lime-500
];

export default function Roulette({ items }: RouletteProps) {
  const [spinning, setSpinning] = useState(false);
  const [winner, setWinner] = useState<RouletteItem | null>(null);
  const controls = useAnimation();
  const rotationRef = useRef(0);

  const displayItems = items.length > 0 ? items.slice(0, 8) : [];
  const segAngle = 360 / Math.max(displayItems.length, 1);

  const spin = async () => {
    if (spinning || displayItems.length === 0) return;

    setSpinning(true);
    setWinner(null);

    const randomOffset = Math.random() * 360;
    const targetRotation = rotationRef.current + 1800 + randomOffset;

    await controls.start({
      rotate: targetRotation,
      transition: {
        duration: 4,
        ease: [0.2, 0.8, 0.3, 1],
        type: "tween"
      }
    });

    rotationRef.current = targetRotation;

    const degreesRotated = targetRotation % 360;
    const angleUnderPointer = (360 - degreesRotated) % 360;
    const winningIndexCalc = Math.floor(angleUnderPointer / segAngle);

    const actualWinnerIndex = winningIndexCalc < 0 ? 0 : winningIndexCalc >= displayItems.length ? displayItems.length - 1 : winningIndexCalc;

    setWinner(displayItems[actualWinnerIndex]);
    setSpinning(false);
  };

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ko-KR';
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  if (displayItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] py-12">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
            <span className="text-6xl">🎡</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-700 mb-2">돌릴 문장이 없어요!</h3>
          <p className="text-gray-500">설정에서 문장을 먼저 만들어주세요.</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-8 relative">
      {/* Winner Modal */}
      <AnimatePresence>
        {winner && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-md p-4"
            onClick={() => setWinner(null)}
          >
            <motion.div
              initial={{ scale: 0.5, y: 100 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.5, y: 100 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-center relative overflow-hidden">
                <motion.div
                  className="absolute inset-0"
                  animate={{
                    background: [
                      'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%)',
                      'linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%)',
                    ]
                  }}
                  transition={{ repeat: Infinity, duration: 2 }}
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1], rotate: [0, 10, -10, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="text-6xl mb-2"
                >
                  🎉
                </motion.div>
                <h2 className="text-2xl font-bold text-white">당첨!</h2>
              </div>

              {/* Content */}
              <div className="p-8 text-center">
                <p className="text-3xl font-bold text-gray-800 leading-relaxed break-keep mb-6">
                  {winner.text}
                </p>

                <div className="flex justify-center gap-3">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => speakText(winner.text)}
                    className="flex items-center gap-2 px-6 py-3 bg-purple-100 text-purple-700 rounded-xl font-bold hover:bg-purple-200 transition-colors"
                  >
                    <Volume2 size={20} />
                    듣기
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setWinner(null)}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
                  >
                    <RotateCcw size={20} />
                    한 번 더!
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Roulette Wheel */}
      <div className="relative mb-8">
        {/* Pointer */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-4 z-20">
          <motion.div
            animate={spinning ? { y: [0, -5, 0] } : {}}
            transition={{ repeat: spinning ? Infinity : 0, duration: 0.3 }}
            className="w-0 h-0 border-l-[20px] border-r-[20px] border-t-[32px] border-l-transparent border-r-transparent border-t-purple-600 filter drop-shadow-lg"
          />
        </div>

        {/* Wheel Container */}
        <div className="relative w-[300px] h-[300px] md:w-[420px] md:h-[420px]">
          {/* Outer Ring */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-200 to-pink-200 p-2 shadow-2xl">
            <motion.div
              animate={controls}
              className="w-full h-full rounded-full bg-white overflow-hidden relative shadow-inner"
            >
              {/* SVG Wheel */}
              <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                <defs>
                  {displayItems.map((_, index) => (
                    <linearGradient
                      key={`grad-${index}`}
                      id={`gradient-${index}`}
                      x1="0%" y1="0%" x2="100%" y2="100%"
                    >
                      <stop offset="0%" stopColor={COLORS[index % COLORS.length]} />
                      <stop offset="100%" stopColor={COLORS[(index + 1) % COLORS.length]} stopOpacity="0.8" />
                    </linearGradient>
                  ))}
                </defs>
                {displayItems.map((item, index) => {
                  const startAngle = (index * 360) / displayItems.length;
                  const endAngle = ((index + 1) * 360) / displayItems.length;

                  const startRad = (startAngle * Math.PI) / 180;
                  const endRad = (endAngle * Math.PI) / 180;

                  const x1 = 50 + 50 * Math.cos(startRad);
                  const y1 = 50 + 50 * Math.sin(startRad);
                  const x2 = 50 + 50 * Math.cos(endRad);
                  const y2 = 50 + 50 * Math.sin(endRad);

                  const largeArcFlag = segAngle > 180 ? 1 : 0;
                  const pathData = `M 50 50 L ${x1} ${y1} A 50 50 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

                  return (
                    <path
                      key={item.id}
                      d={pathData}
                      fill={COLORS[index % COLORS.length]}
                      stroke="white"
                      strokeWidth="0.5"
                    />
                  );
                })}
              </svg>

              {/* Text Labels */}
              {displayItems.map((item, index) => {
                const angle = index * segAngle + segAngle / 2;
                return (
                  <div
                    key={'text-' + item.id}
                    className="absolute w-[40%] h-8 flex items-center justify-end pr-2"
                    style={{
                      top: '50%',
                      left: '50%',
                      transform: `rotate(${angle - 90}deg) translateX(10%)`,
                      transformOrigin: 'left center',
                      marginTop: '-1rem',
                    }}
                  >
                    <span className="truncate max-w-[100px] md:max-w-[140px] text-white font-bold text-xs md:text-sm drop-shadow-lg">
                      {item.text}
                    </span>
                  </div>
                );
              })}
            </motion.div>
          </div>

          {/* Center Button */}
          <motion.div
            whileHover={!spinning ? { scale: 1.1 } : {}}
            whileTap={!spinning ? { scale: 0.95 } : {}}
            onClick={spin}
            className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 md:w-24 md:h-24 rounded-full shadow-xl z-10 flex items-center justify-center cursor-pointer transition-all ${
              spinning
                ? 'bg-gray-200'
                : 'bg-gradient-to-br from-purple-500 to-pink-500 hover:shadow-2xl'
            }`}
          >
            {spinning ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                className="text-3xl"
              >
                ⭐
              </motion.div>
            ) : (
              <Sparkles size={32} className="text-white" />
            )}
          </motion.div>
        </div>
      </div>

      {/* Spin Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={spin}
        disabled={spinning}
        className={`px-10 py-4 rounded-2xl text-xl font-bold shadow-xl transition-all ${
          spinning
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-2xl hover:from-purple-600 hover:to-pink-600'
        }`}
      >
        {spinning ? (
          <span className="flex items-center gap-2">
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            >
              🎡
            </motion.span>
            돌아가는 중...
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <Sparkles size={24} />
            돌려 돌려!
          </span>
        )}
      </motion.button>

      {/* Item count indicator */}
      <p className="mt-4 text-sm text-gray-400">
        {displayItems.length}개 문장 중 랜덤 선택
      </p>
    </div>
  );
}
