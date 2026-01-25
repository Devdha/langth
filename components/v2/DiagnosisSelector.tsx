"use client";

import { DiagnosisType, TherapyApproach } from "@/types/v2";

interface DiagnosisSelectorProps {
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  onDiagnosisChange: (diagnosis: DiagnosisType) => void;
  onApproachChange: (approach: TherapyApproach) => void;
}

// 접근법 우선 선택 - 진단군은 자동 매핑
// Note: minimal_pairs and maximal_oppositions are planned for a separate word-pair discrimination mode
const THERAPY_APPROACHES = [
  {
    id: 'complexity' as const,
    label: '복잡성 접근',
    desc: '목표 음소가 포함된 문장 생성 (난이도별)',
    category: 'SSD 치료',
    defaultDiagnosis: 'SSD' as const,
    bgColor: 'bg-indigo-500',
  },
  {
    id: 'core_vocabulary' as const,
    label: '핵심어휘',
    desc: '고빈도 기능어 중심 문장',
    category: 'ASD/LD 치료',
    defaultDiagnosis: 'ASD' as const,
    bgColor: 'bg-pink-500',
  },
];

export default function DiagnosisSelector({
  diagnosis,
  therapyApproach,
  onDiagnosisChange,
  onApproachChange,
}: DiagnosisSelectorProps) {
  const handleApproachChange = (approach: TherapyApproach) => {
    onApproachChange(approach);
    // 접근법에 따라 진단군 자동 설정
    const approachConfig = THERAPY_APPROACHES.find(a => a.id === approach);
    if (approachConfig) {
      onDiagnosisChange(approachConfig.defaultDiagnosis);
    }
  };

  // 카테고리별 그룹핑
  const categories = [
    { name: 'SSD 치료', approaches: THERAPY_APPROACHES.filter(a => a.category === 'SSD 치료') },
    { name: 'ASD/LD 치료', approaches: THERAPY_APPROACHES.filter(a => a.category === 'ASD/LD 치료') },
  ];

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-bold text-gray-600">치료 접근법</h4>

      {categories.map((category) => (
        <div key={category.name}>
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wide">{category.name}</div>
          <div className="space-y-2">
            {category.approaches.map((a) => (
              <button
                key={a.id}
                onClick={() => handleApproachChange(a.id)}
                className={`w-full p-3 rounded-xl border-2 transition-all text-left relative overflow-hidden ${
                  therapyApproach === a.id
                    ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                    : 'border-gray-100 hover:border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-800 text-sm">{a.label}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{a.desc}</div>
                  </div>
                  {therapyApproach === a.id && (
                    <div className="w-5 h-5 rounded-full bg-purple-500 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
