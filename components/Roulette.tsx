"use client";

import { useState, useRef } from "react";
import { motion, useAnimation, AnimatePresence } from "framer-motion";
import { TherapyItem } from "@/types";

interface RouletteProps {
  items: TherapyItem[];
}

const COLORS = ['#ff9f43', '#ee5a6f', '#4ecdc4', '#95e1d3', '#a8d8ea', '#f38181', '#ffeaa7', '#dfe6e9'];

export default function Roulette({ items }: RouletteProps) {
  const [spinning, setSpinning] = useState(false);
  const [winner, setWinner] = useState<TherapyItem | null>(null);
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

  if (displayItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
        <div className="text-8xl mb-4 opacity-20">🎡</div>
        <p className="text-xl text-gray-400 font-bold">돌릴 문장이 없어요!</p>
        <p className="text-gray-400">설정에서 문장을 먼저 만들어주세요.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-10 relative overflow-hidden">
      <AnimatePresence>
        {winner && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
            onClick={() => setWinner(null)}
          >
            <motion.div 
              initial={{ y: 50 }}
              animate={{ y: 0, rotate: [0, -5, 5, 0] }}
              className="bg-white rounded-3xl p-10 shadow-2xl max-w-lg w-full text-center border-8 border-accent relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-4 bg-accent/20" />
              <motion.div 
                animate={{ scale: [1, 1.2, 1], rotate: [0, 10, -10, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="text-6xl mb-6"
              >
                🎉
              </motion.div>
              <h2 className="text-3xl font-bold text-primary mb-4">짜잔!</h2>
              <p className="text-4xl font-bold text-gray-800 leading-snug break-keep">
                {winner.text}
              </p>
              <button 
                className="mt-8 px-8 py-3 bg-primary text-white rounded-xl font-bold text-xl shadow-lg hover:bg-primary/90 transition-transform hover:scale-105"
                onClick={(e) => {
                  e.stopPropagation();
                  setWinner(null);
                }}
              >
                한 번 더!
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative mb-10 group">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-6 z-20 w-12 h-14 filter drop-shadow-lg">
           <svg viewBox="0 0 24 24" fill="currentColor" className="text-primary">
             <path d="M12 22L2 2h20L12 22z" />
           </svg>
        </div>

        <div className="relative w-[320px] h-[320px] md:w-[500px] md:h-[500px]">
          <motion.div
            animate={controls}
            className="w-full h-full rounded-full border-8 border-white shadow-2xl bg-white overflow-hidden relative"
          >
            {displayItems.map((item, index) => {
              const rotation = index * segAngle; 
              return (
                <div
                  key={item.id}
                  className="absolute top-0 left-1/2 w-full h-full origin-left"
                  style={{
                    transform: `rotate(${rotation - 90 + (segAngle/2)}deg)`, 
                    transformOrigin: "50% 50%", 
                  }}
                />
              );
            })}
            
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
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
                  <g key={item.id}>
                    <path d={pathData} fill={COLORS[index % COLORS.length]} stroke="white" strokeWidth="0.5" />
                  </g>
                );
              })}
            </svg>
            
            {displayItems.map((item, index) => {
               const angle = index * segAngle + segAngle / 2;
               return (
                 <div
                   key={'text-' + item.id}
                   className="absolute top-1/2 left-1/2 w-[45%] h-8 -mt-4 origin-left flex items-center justify-end pr-4 text-white font-bold text-sm md:text-lg shadow-sm"
                   style={{
                     transform: `rotate(${angle - 90}deg) translate(20px, 0)`,
                     textAlign: 'right',
                     transformOrigin: "center left",
                     left: '50%',
                     top: '50%'
                   }}
                 >
                   <span className="truncate max-w-[120px] md:max-w-[180px] drop-shadow-md">
                     {item.text}
                   </span>
                 </div>
               );
            })}
          </motion.div>
          
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-white rounded-full shadow-lg border-4 border-gray-100 z-10 flex items-center justify-center">
            <div className="text-2xl">😊</div>
          </div>
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={spin}
        disabled={spinning}
        className={`px-12 py-5 rounded-full text-2xl font-black text-white shadow-xl transition-all ${
          spinning 
            ? 'bg-gray-300 cursor-not-allowed' 
            : 'bg-gradient-to-r from-primary to-warning hover:shadow-2xl border-b-8 border-orange-700 active:border-b-0 active:translate-y-2'
        }`}
      >
        {spinning ? '돌아가는 중...' : '돌려 돌려!'}
      </motion.button>
    </div>
  );
}
