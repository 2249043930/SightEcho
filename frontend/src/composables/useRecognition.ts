/**
 * composables/useRecognition.ts
 * 通用识别业务逻辑：调用 /api/v1/recognition/{type}、管理 loading、结果写入 store
 */
import { ref } from 'vue';
import { recognize, type RecognitionType, type RecognitionResult } from '@/api/recognition';
import { useRecognitionStore } from '@/stores/recognition';

export function useRecognition(type: RecognitionType) {
  const store = useRecognitionStore();
  const loading = ref(false);
  const result = ref<RecognitionResult | null>(null);
  const error = ref<string | null>(null);

  async function submit(blob: Blob, extra?: Record<string, any>) {
    loading.value = true;
    error.value = null;
    try {
      const r = await recognize({ type, image: blob, extra });
      result.value = r;
      store.setCurrent(r);
      store.prependHistory(r);
      return r;
    } catch (e: any) {
      error.value = e?.message || '识别失败，请重试';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function reset() {
    result.value = null;
    error.value = null;
  }

  return { loading, result, error, submit, reset };
}
