<script setup lang="ts">
/**
 * components/business/VoiceButton.vue
 * 语音按钮：长按录音、短按取消、松手发送
 */
import { ref, computed } from 'vue';
import { useLongPress } from '@/composables/useLongPress';
import { useTTS } from '@/composables/useTTS';

const props = withDefaults(
  defineProps<{
    size?: 'small' | 'medium' | 'large';
    label?: string;
  }>(),
  { size: 'large', label: '长按开始语音输入' },
);

const emit = defineEmits<{
  (e: 'start'): void;
  (e: 'send', text: string): void;
  (e: 'cancel'): void;
  (e: 'recognized', text: string): void;
}>();

const isRecording = ref(false);
const interim = ref('');
const finalText = ref('');

const { speak } = useTTS();

let recognition: any = null;
let active = false;

const sizeMap = {
  small: 72,
  medium: 96,
  large: 128,
};
const btnSize = computed(() => sizeMap[props.size]);

function initSR() {
  if (recognition) return;
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SR) {
    console.warn('浏览器不支持 SpeechRecognition');
    return;
  }
  recognition = new SR();
  recognition.lang = 'zh-CN';
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.onresult = (e: any) => {
    let interimText = '';
    let finalT = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) finalT += t;
      else interimText += t;
    }
    if (interimText) interim.value = interimText;
    if (finalT) {
      finalText.value += finalT;
      emit('recognized', finalText.value);
    }
  };
  recognition.onerror = (e: any) => {
    console.warn('语音识别错误：', e.error);
  };
  recognition.onend = () => {
    if (active) {
      try { recognition.start(); } catch { /* ignore */ }
    }
  };
}

function start() {
  initSR();
  if (!recognition) return;
  active = true;
  isRecording.value = true;
  finalText.value = '';
  interim.value = '';
  try { recognition.start(); } catch (e) { console.warn(e); }
  emit('start');
}

function send() {
  if (!isRecording.value) return;
  const text = (finalText.value + interim.value).trim();
  active = false;
  isRecording.value = false;
  if (recognition) {
    try { recognition.stop(); } catch { /* ignore */ }
  }
  if (text) {
    emit('send', text);
  } else {
    speak('没有识别到内容，请重试');
    emit('cancel');
  }
}

function cancel() {
  active = false;
  isRecording.value = false;
  if (recognition) {
    try { recognition.stop(); } catch { /* ignore */ }
  }
  emit('cancel');
}

const longPress = useLongPress({
  duration: 300,
  onStart: () => {
    if (!isRecording.value) start();
  },
  onLongPress: () => {
    /* 触发后保持 */
  },
  onEnd: () => {
    if (isRecording.value) send();
  },
  onCancel: () => {
    if (isRecording.value) cancel();
  },
});
</script>

<template>
  <div class="voice-button-wrap" :style="{ width: btnSize + 'px', height: btnSize + 'px' }">
    <button
      class="voice-button"
      :class="{ recording: isRecording }"
      :style="{ width: btnSize + 'px', height: btnSize + 'px' }"
      :aria-label="label"
      :aria-pressed="isRecording"
      :aria-describedby="isRecording ? 'voice-status' : undefined"
      role="button"
      v-on="longPress.events"
    >
      <span v-if="!isRecording" class="mic-icon" aria-hidden="true">🎙</span>
      <span v-else class="wave-icon" aria-hidden="true">
        <span /><span /><span /><span /><span />
      </span>
    </button>
    <span v-if="isRecording" id="voice-status" class="sr-only" aria-live="assertive">
      正在录音，松开发送，按 Esc 取消
    </span>
    <p v-if="isRecording && (finalText + interim)" class="voice-text" aria-live="polite">
      {{ finalText + interim }}
    </p>
    <p v-else class="voice-hint">{{ label }}</p>
  </div>
</template>

<style lang="scss" scoped>
.voice-button-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.voice-button {
  background: $bg-main;
  border: 0;
  border-radius: 50%;
  box-shadow: 10px 10px 20px $shadow-dark, -10px -10px 20px $shadow-light;
  color: $text-main;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-base;
  font-size: 32px;
  &:hover {
    box-shadow: 6px 6px 12px $shadow-dark, -6px -6px 12px $shadow-light;
  }
  &:active,
  &:focus-visible {
    box-shadow: inset 6px 6px 12px $shadow-dark, inset -6px -6px 12px $shadow-light;
    outline: 2px solid $accent;
    outline-offset: 4px;
  }
  &.recording {
    color: $accent;
    box-shadow: inset 6px 6px 12px $shadow-dark, inset -6px -6px 12px $shadow-light;
  }
}
.mic-icon { font-size: 40px; }
.wave-icon {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 32px;
  span {
    display: block;
    width: 4px;
    background: $accent;
    border-radius: 2px;
    animation: wave 1s ease-in-out infinite;
    &:nth-child(1) { height: 16px; animation-delay: 0s; }
    &:nth-child(2) { height: 28px; animation-delay: 0.1s; }
    &:nth-child(3) { height: 20px; animation-delay: 0.2s; }
    &:nth-child(4) { height: 32px; animation-delay: 0.3s; }
    &:nth-child(5) { height: 18px; animation-delay: 0.4s; }
  }
}
@keyframes wave {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
}
.voice-hint, .voice-text {
  font-size: 14px;
  color: $text-secondary;
  text-align: center;
  margin: 0;
  max-width: 280px;
}
.voice-text {
  color: $text-main;
  font-weight: 500;
}
</style>
