<script setup lang="ts">
/**
 * components/business/ResultDisplay.vue
 * 识别结果展示
 */
import { computed } from 'vue';
import AudioPlayer from './AudioPlayer.vue';
import { useSettingsStore } from '@/stores/settings';
import { useTTS } from '@/composables/useTTS';

const props = defineProps<{
  title?: string;
  content?: string;
  audioUrl?: string;
  loading?: boolean;
  empty?: boolean;
}>();

const settings = useSettingsStore();
const { speak } = useTTS();

const showAutoPlay = computed(() => settings.autoAnnounce && !!props.content);

function handleReplay() {
  if (props.content) speak(props.content);
}
</script>

<template>
  <div class="result-display" role="region" :aria-label="title || '识别结果'">
    <header class="result-header">
      <h2 class="result-title">{{ title || '识别结果' }}</h2>
      <AudioPlayer
        v-if="audioUrl"
        :audio-url="audioUrl"
        :auto-play="showAutoPlay"
      />
      <button
        v-else-if="content"
        class="replay-btn"
        aria-label="重新播报结果"
        @click="handleReplay"
      >
        <el-icon :size="16"><VideoPlay /></el-icon>
        <span>重听</span>
      </button>
    </header>

    <div class="result-body">
      <div v-if="loading" class="result-loading" aria-busy="true">
        <div class="loading-spinner" aria-hidden="true" />
        <p>正在识别中，请稍候…</p>
      </div>
      <div v-else-if="empty || !content" class="result-empty">
        <el-icon :size="48" aria-hidden="true"><Picture /></el-icon>
        <p>暂无识别结果</p>
        <p class="hint">点击「拍照」按钮或长按语音键开始识别</p>
      </div>
      <p v-else class="result-content" aria-live="polite">{{ content }}</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.result-display {
  display: flex;
  flex-direction: column;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  height: 100%;
  overflow: hidden;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: $bg-elevated;
  border-bottom: 1px solid rgba(184, 188, 194, 0.3);
}
.result-title {
  font-size: 18px;
  font-weight: 600;
  color: $text-main;
  margin: 0;
}
.replay-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 36px;
  padding: 0 12px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 13px;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.result-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-height: 240px;
}
.result-loading, .result-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  color: $text-secondary;
  min-height: 200px;
  p { margin: 0; }
  .hint { font-size: 13px; color: $text-muted; }
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid $shadow-dark;
  border-top-color: $accent;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.result-content {
  font-size: 18px;
  line-height: 1.7;
  color: $text-main;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>
