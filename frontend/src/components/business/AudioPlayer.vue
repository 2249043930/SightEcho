<script setup lang="ts">
/**
 * components/business/AudioPlayer.vue
 * TTS 播报组件
 */
import { ref, onBeforeUnmount } from 'vue';
import { useTTS } from '@/composables/useTTS';
import { playBase64Audio } from '@/utils/audio';

const props = withDefaults(
  defineProps<{
    text?: string;
    audioUrl?: string;
    autoPlay?: boolean;
  }>(),
  { autoPlay: false },
);

const { isSpeaking, lastText, speak, stop } = useTTS();
const localAudio = ref<HTMLAudioElement | null>(null);

async function play() {
  if (props.audioUrl) {
    // 服务端 TTS 音频
    if (localAudio.value) localAudio.value.pause();
    localAudio.value = new Audio(props.audioUrl);
    localAudio.value.play().catch((e) => console.error('音频播放失败：', e));
  } else if (props.text) {
    speak(props.text);
  }
}

function pause() {
  if (localAudio.value) {
    localAudio.value.pause();
  }
  stop();
}

if (props.autoPlay && (props.audioUrl || props.text)) {
  setTimeout(play, 100);
}

onBeforeUnmount(() => {
  if (localAudio.value) localAudio.value.pause();
});
</script>

<template>
  <div class="audio-player" role="region" aria-label="语音播报">
    <button
      class="player-btn"
      :aria-label="isSpeaking ? '停止播报' : '播放语音'"
      :aria-pressed="isSpeaking"
      @click="isSpeaking ? pause() : play()"
    >
      <el-icon :size="20">
        <component :is="isSpeaking ? 'VideoPause' : 'VideoPlay'" />
      </el-icon>
      <span>{{ isSpeaking ? '停止' : '播放' }}</span>
    </button>
    <span v-if="lastText" class="sr-only" aria-live="polite">正在播报：{{ lastText }}</span>
  </div>
</template>

<style lang="scss" scoped>
.audio-player {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.player-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 14px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
</style>
