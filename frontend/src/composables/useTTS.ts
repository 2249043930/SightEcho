/**
 * composables/useTTS.ts
 * TTS 播报：浏览器原生 SpeechSynthesis + 可选后端 WS 流式
 */
import { ref, onBeforeUnmount } from 'vue';
import { useSettingsStore } from '@/stores/settings';

export function useTTS() {
  const settings = useSettingsStore();
  const isSpeaking = ref(false);
  const lastText = ref('');

  function isSupported(): boolean {
    return typeof window !== 'undefined' && 'speechSynthesis' in window;
  }

  function speak(text: string, opts: { interrupt?: boolean } = { interrupt: true }) {
    if (!text) return;
    if (!isSupported()) {
      console.warn('当前浏览器不支持 TTS');
      return;
    }
    lastText.value = text;
    if (opts.interrupt) {
      window.speechSynthesis.cancel();
    }
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'zh-CN';
    utter.rate = settings.speed;
    utter.volume = settings.volume / 100;
    utter.onstart = () => (isSpeaking.value = true);
    utter.onend = () => (isSpeaking.value = false);
    utter.onerror = () => (isSpeaking.value = false);
    // 选中文语音
    const voices = window.speechSynthesis.getVoices();
    const zh = voices.find((v) => v.lang.toLowerCase().startsWith('zh'));
    if (zh) utter.voice = zh;
    window.speechSynthesis.speak(utter);
  }

  function stop() {
    if (isSupported()) window.speechSynthesis.cancel();
    isSpeaking.value = false;
  }

  onBeforeUnmount(stop);

  return { isSpeaking, lastText, isSupported, speak, stop };
}
