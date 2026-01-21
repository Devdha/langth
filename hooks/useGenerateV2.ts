"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  GameSettingsV2,
  TherapyItemV2,
  GenerateRequestV2,
  GenerateResponseV2,
  ErrorResponseV2,
} from "@/types/v2";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const LOADING_TIMEOUT = 60000; // 60 seconds for v2 pipeline

interface GenerateMeta {
  requestedCount: number;
  generatedCount: number;
  averageScore: number;
  processingTimeMs: number;
}

interface UseGenerateV2Result {
  generate: (settings: GameSettingsV2) => Promise<void>;
  cancel: () => void;
  loading: boolean;
  error: string | null;
  items: TherapyItemV2[];
  warning: string | null;
  meta: GenerateMeta | null;
  clearWarning: () => void;
}

export function useGenerateV2(
  onSuccess?: (items: TherapyItemV2[]) => void,
): UseGenerateV2Result {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<TherapyItemV2[]>([]);
  const [warning, setWarning] = useState<string | null>(null);
  const [meta, setMeta] = useState<GenerateMeta | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
      }
    };
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }
    setLoading(false);
  }, []);

  const clearWarning = useCallback(() => {
    setWarning(null);
  }, []);

  const generate = useCallback(async (settings: GameSettingsV2) => {
    // Reset state
    setLoading(true);
    setError(null);
    setWarning(null);
    setMeta(null);

    // Setup AbortController and timeout
    abortControllerRef.current = new AbortController();
    timeoutIdRef.current = setTimeout(() => {
      abortControllerRef.current?.abort();
    }, LOADING_TIMEOUT);

    try {
      // Map GameSettingsV2 to GenerateRequestV2
      const requestBody: GenerateRequestV2 = {
        language: settings.language,
        age: settings.age,
        count: settings.count,
        target: settings.target,
        sentenceLength: settings.sentenceLength,
        diagnosis: settings.diagnosis,
        therapyApproach: settings.therapyApproach,
        theme: settings.theme || undefined,
        communicativeFunction: settings.communicativeFunction || undefined,
      };

      const res = await fetch(`${API_BASE_URL}/api/v2/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });

      // Clear timeout after successful response
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }

      const data: GenerateResponseV2 | ErrorResponseV2 = await res.json();

      if (res.ok && data.success) {
        const responseData = data.data;
        setItems(responseData.items);
        setMeta(responseData.meta);

        // Show warning if fewer items generated than requested
        if (responseData.meta.generatedCount < settings.count) {
          setWarning(
            `요청한 ${settings.count}개 중 ${responseData.meta.generatedCount}개만 생성되었습니다. 조건에 맞는 문장이 부족할 수 있습니다.`
          );
        }

        // Call success callback if provided
        if (onSuccess) {
          onSuccess(responseData.items);
        }
      } else if (!data.success) {
        const errorMessage = data.error.message || '문장 생성에 실패했습니다. 다시 시도해주세요.';
        setError(errorMessage);
        setItems([]);
      } else {
        // Unexpected response format
        setError('서버 응답 형식이 올바르지 않습니다.');
        setItems([]);
      }
    } catch (err) {
      // Clear timeout on error
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }

      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          setError('요청 시간이 초과되었습니다. 다시 시도해주세요.');
        } else if (err.message.includes('fetch')) {
          setError('서버 연결에 실패했습니다. 네트워크 상태를 확인해주세요.');
        } else {
          setError('알 수 없는 오류가 발생했습니다. 다시 시도해주세요.');
        }
      } else {
        setError('서버 연결에 실패했습니다. 다시 시도해주세요.');
      }
      setItems([]);
      console.error("Failed to generate", err);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [onSuccess]);

  return {
    generate,
    cancel,
    loading,
    error,
    items,
    warning,
    meta,
    clearWarning,
  };
}
