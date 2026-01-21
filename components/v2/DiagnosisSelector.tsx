"use client";

import { DiagnosisType, TherapyApproach } from "@/types/v2";

interface DiagnosisSelectorProps {
  diagnosis: DiagnosisType;
  therapyApproach: TherapyApproach;
  onDiagnosisChange: (diagnosis: DiagnosisType) => void;
  onApproachChange: (approach: TherapyApproach) => void;
}

const DIAGNOSES = [
  { id: 'SSD' as const, label: '말소리장애', desc: 'Speech Sound Disorder', color: 'bg-purple-500' },
  { id: 'ASD' as const, label: '자폐스펙트럼', desc: 'Autism Spectrum', color: 'bg-indigo-500' },
  { id: 'LD' as const, label: '언어발달지연', desc: 'Language Delay', color: 'bg-pink-500' },
];

const THERAPY_APPROACHES: Record<DiagnosisType, { id: TherapyApproach; label: string; desc: string }[]> = {
  SSD: [
    { id: 'minimal_pairs', label: '최소대립쌍', desc: 'Minimal Pairs' },
    { id: 'maximal_oppositions', label: '최대대립쌍', desc: 'Maximal Oppositions' },
    { id: 'complexity', label: '복잡성 접근', desc: 'Complexity Approach' },
  ],
  ASD: [
    { id: 'core_vocabulary', label: '핵심어휘', desc: 'Core Vocabulary' },
  ],
  LD: [
    { id: 'core_vocabulary', label: '핵심어휘', desc: 'Core Vocabulary' },
  ],
};

export default function DiagnosisSelector({
  diagnosis,
  therapyApproach,
  onDiagnosisChange,
  onApproachChange,
}: DiagnosisSelectorProps) {
  const handleDiagnosisChange = (newDiagnosis: DiagnosisType) => {
    onDiagnosisChange(newDiagnosis);
    // Auto-select first available approach for the new diagnosis
    const approaches = THERAPY_APPROACHES[newDiagnosis];
    if (approaches.length > 0 && !approaches.find(a => a.id === therapyApproach)) {
      onApproachChange(approaches[0].id);
    }
  };

  const availableApproaches = THERAPY_APPROACHES[diagnosis];

  return (
    <div className="space-y-6">
      {/* Diagnosis Selection */}
      <div>
        <h4 className="text-sm font-bold text-gray-600 mb-3">진단군</h4>
        <div className="grid grid-cols-3 gap-3">
          {DIAGNOSES.map((d) => (
            <button
              key={d.id}
              onClick={() => handleDiagnosisChange(d.id)}
              className={`p-3 rounded-xl border-2 transition-all text-left relative overflow-hidden ${
                diagnosis === d.id
                  ? 'border-transparent ring-4 ring-opacity-50'
                  : 'border-gray-100 hover:border-gray-200 bg-white'
              } ${diagnosis === d.id ? 'ring-' + d.color.replace('bg-', '') : ''}`}
            >
              <div className={`absolute inset-0 opacity-10 ${d.color}`} />
              {diagnosis === d.id && (
                <div className={`absolute inset-0 opacity-20 ${d.color}`} />
              )}
              <div className="relative">
                <div className="font-bold text-gray-800 text-sm">{d.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{d.desc}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Therapy Approach Selection */}
      <div>
        <h4 className="text-sm font-bold text-gray-600 mb-3">치료 접근법</h4>
        <div className="grid grid-cols-1 gap-2">
          {availableApproaches.map((a) => (
            <button
              key={a.id}
              onClick={() => onApproachChange(a.id)}
              className={`p-3 rounded-xl border-2 transition-all text-left ${
                therapyApproach === a.id
                  ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                  : 'border-gray-100 hover:border-gray-200 bg-white'
              }`}
            >
              <div className="font-bold text-gray-800 text-sm">{a.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{a.desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
