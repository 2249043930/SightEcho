/**
 * stores/recognition.ts
 * 识别结果状态
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';

export type RecognitionType = 'travel' | 'ocr' | 'currency' | 'product' | 'face';

export interface RecognitionItem {
  id: string;
  type: RecognitionType;
  title: string;
  content: string;
  thumbnail?: string;
  audioUrl?: string;
  createdAt: string;
}

export const useRecognitionStore = defineStore('recognition', () => {
  const current = ref<RecognitionItem | null>(null);
  const history = ref<RecognitionItem[]>([]);
  const loading = ref(false);
  const lastError = ref<string | null>(null);

  function setCurrent(item: RecognitionItem | null) {
    current.value = item;
  }
  function setHistory(list: RecognitionItem[]) {
    history.value = list;
  }
  function prependHistory(item: RecognitionItem) {
    history.value = [item, ...history.value];
  }
  function removeHistory(id: string) {
    history.value = history.value.filter((h) => h.id !== id);
  }
  function clearHistory() {
    history.value = [];
  }
  function setLoading(v: boolean) {
    loading.value = v;
  }
  function setError(msg: string | null) {
    lastError.value = msg;
  }

  return {
    current,
    history,
    loading,
    lastError,
    setCurrent,
    setHistory,
    prependHistory,
    removeHistory,
    clearHistory,
    setLoading,
    setError,
  };
});
