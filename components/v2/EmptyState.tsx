"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";

interface EmptyStateProps {
  onNewSession: () => void;
  hasExistingSessions: boolean;
}

export default function EmptyState({
  onNewSession,
  hasExistingSessions,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
    >
      {/* Hero Icon */}
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: "spring" }}
        className="w-32 h-32 bg-gradient-to-br from-purple-500 to-pink-500 rounded-3xl flex items-center justify-center mb-8 shadow-2xl shadow-purple-500/30"
      >
        <span className="text-6xl">🎯</span>
      </motion.div>

      {/* Title */}
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-3xl font-bold text-gray-800 mb-4"
      >
        {hasExistingSessions
          ? "세션을 선택하세요"
          : "말놀이 자판기 V2에 오신 것을 환영합니다"}
      </motion.h1>

      {/* Description */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-gray-500 max-w-md mb-8 leading-relaxed"
      >
        {hasExistingSessions
          ? "왼쪽 사이드바에서 기존 세션을 선택하거나, 새 세션을 만들어보세요."
          : "AI 기반 언어치료 문장 생성 서비스입니다. 새 세션을 만들어 치료 문장을 생성해보세요."}
      </motion.p>

      {/* CTA Button */}
      <motion.button
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        onClick={onNewSession}
        className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-2xl font-bold text-lg shadow-xl shadow-purple-500/30 hover:shadow-2xl hover:shadow-purple-500/40 transition-all hover:-translate-y-1"
      >
        <Sparkles size={24} />
        새 세션 시작하기
        <ArrowRight
          size={20}
          className="group-hover:translate-x-1 transition-transform"
        />
      </motion.button>

      {/* Feature highlights */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-3xl"
      >
        {[
          {
            icon: "🎯",
            title: "목표 음소 설정",
            desc: "한국어/영어 음소와 위치 선택",
          },
          {
            icon: "🧠",
            title: "AI 기반 생성",
            desc: "GPT-4o가 치료에 적합한 문장 생성",
          },
          {
            icon: "📊",
            title: "세션 관리",
            desc: "환자별 세션 저장 및 관리",
          },
        ].map((feature, i) => (
          <div
            key={i}
            className="bg-white/50 backdrop-blur rounded-2xl p-6 text-center"
          >
            <div className="text-4xl mb-3">{feature.icon}</div>
            <h3 className="font-bold text-gray-800 mb-1">{feature.title}</h3>
            <p className="text-sm text-gray-500">{feature.desc}</p>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
