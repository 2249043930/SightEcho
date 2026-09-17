/**
 * composables/useVoiceInput.ts
 * 语音输入：基于 Web Speech API
 * 用于邮箱地址、验证码等文本输入
 */
import { ref, onBeforeUnmount } from 'vue';

export interface UseVoiceInputOptions {
  lang?: string;
  /** 识别完成回调 */
  onResult?: (text: string, isFinal: boolean) => void;
  /** 错误回调 */
  onError?: (error: string) => void;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}) {
  const { lang = 'zh-CN', onResult, onError } = options;

  const isListening = ref(false);
  const transcript = ref('');
  const interim = ref('');
  const error = ref<string | null>(null);
  const supported = ref(false);

  let recognition: any = null;
  let active = false;

  function init() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      supported.value = false;
      error.value = '当前浏览器不支持语音识别，请使用 Chrome / Edge';
      return false;
    }
    supported.value = true;
    recognition = new SR();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (e: any) => {
      let interimText = '';
      let finalText = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t;
        else interimText += t;
      }
      interim.value = interimText;
      if (finalText) {
        transcript.value += finalText;
        onResult?.(finalText, true);
      } else if (interimText) {
        onResult?.(interimText, false);
      }
    };
    recognition.onerror = (e: any) => {
      const msg = e.error || '语音识别错误';
      error.value = msg;
      onError?.(msg);
      isListening.value = false;
    };
    recognition.onend = () => {
      isListening.value = false;
      active = false;
    };
    return true;
  }

  function start() {
    if (isListening.value) return;
    if (!recognition && !init()) return;
    transcript.value = '';
    interim.value = '';
    error.value = null;
    active = true;
    isListening.value = true;
    try {
      recognition.start();
    } catch (e: any) {
      error.value = e?.message || '启动失败';
      isListening.value = false;
    }
  }

  function stop() {
    active = false;
    isListening.value = false;
    if (recognition) {
      try { recognition.stop(); } catch { /* ignore */ }
    }
  }

  onBeforeUnmount(stop);

  return { isListening, transcript, interim, error, supported, start, stop };
}
