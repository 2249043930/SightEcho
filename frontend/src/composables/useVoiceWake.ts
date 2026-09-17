/**
 * composables/useVoiceWake.ts
 * 语音唤醒：基于 Web Speech API 的 SpeechRecognition
 * 唤醒词：「小昭小昭」/「SightEcho」
 */
import { ref, onBeforeUnmount } from 'vue';

interface UseVoiceWakeOptions {
  wakeWords?: string[];
  onWake?: (transcript: string) => void;
  onCommand?: (transcript: string) => void;
  lang?: string;
}

export function useVoiceWake(options: UseVoiceWakeOptions = {}) {
  const {
    wakeWords = ['小昭小昭', '小昭', 'sightecho', 'xiangzhao'],
    onWake,
    onCommand,
    lang = 'zh-CN',
  } = options;

  const isListening = ref(false);
  const lastTranscript = ref('');
  const error = ref<string | null>(null);

  let recognition: any = null;
  let active = false;

  function init() {
    const SR =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      error.value = '当前浏览器不支持语音识别，请使用 Chrome / Edge';
      return false;
    }
    recognition = new SR();
    recognition.lang = lang;
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: any) => {
      let finalText = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        finalText += event.results[i][0].transcript;
      }
      lastTranscript.value = finalText;
      const lower = finalText.toLowerCase();
      const hit = wakeWords.find((w) => lower.includes(w.toLowerCase()));
      if (hit) {
        onWake?.(finalText);
        // 唤醒后，把唤醒词后的内容视为命令
        const cmd = finalText.split(hit).pop()?.trim();
        if (cmd) onCommand?.(cmd);
      } else {
        onCommand?.(finalText);
      }
    };
    recognition.onerror = (e: any) => {
      error.value = e.error || '语音识别错误';
      if (e.error === 'not-allowed') {
        stop();
      }
    };
    recognition.onend = () => {
      // 连续模式下被浏览器自动结束后重启
      if (active) {
        try {
          recognition.start();
        } catch {
          /* ignore */
        }
      }
    };
    return true;
  }

  function start() {
    if (isListening.value) return;
    if (!recognition && !init()) return;
    active = true;
    try {
      recognition.start();
      isListening.value = true;
    } catch (e) {
      console.warn('启动语音识别失败：', e);
    }
  }

  function stop() {
    active = false;
    isListening.value = false;
    if (recognition) {
      try {
        recognition.stop();
      } catch {
        /* ignore */
      }
    }
  }

  onBeforeUnmount(stop);

  return { isListening, lastTranscript, error, start, stop };
}
