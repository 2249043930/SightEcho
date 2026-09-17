<script setup lang="ts">
/**
 * views/user/Travel.vue
 * 出行感知：识别前方障碍、行人、红绿灯、台阶等
 *
 * 支持两种工作模式：
 *  1. 「拍照模式」（默认）：手动拍一张图片调用 /recognition/travel。
 *  2. 「实时模式」（WebRTC）：摄像头持续抓帧，攒够 4 帧批量调用 /recognition/live，
 *     后端走 JoyAI-VL-Interaction 多帧时序推理；命中危险关键词自动 TTS 播报。
 */
import { computed, ref, onBeforeUnmount, nextTick, watch } from 'vue';
import { useResponsive } from '@/composables/useResponsive';
import { useRecognition } from '@/composables/useRecognition';
import { useLiveStream } from '@/composables/useLiveStream';
import { useTTS } from '@/composables/useTTS';
import CameraCapture from '@/components/business/CameraCapture.vue';
import ResultDisplay from '@/components/business/ResultDisplay.vue';
import EmptyState from '@/components/common/EmptyState.vue';

const { isMobile } = useResponsive();
const { loading, result, submit } = useRecognition('travel');
const tts = useTTS();

// === 模式切换：'photo'（拍照） | 'live'（WebRTC 实时） ===
const mode = ref<'photo' | 'live'>('live');

// === 实时模式 composable（默认参数：每 1s 1 帧，4 帧一批） ===
const liveAll = useLiveStream({
  scene: 'travel',
  facingMode: 'environment',
  frameIntervalMs: 1000,
  batchSize: 4,
  resizeMaxSide: 480,
  quality: 0.6,
  autoSpeak: true,
  onlySpeakDanger: false,  // 出行场景：每批都播，方便视障用户
  saveRecord: true,
});
// 解构出顶层 ref，模板里直接用变量名（Vue 自动 unwrap），TS 也能识别
const {
  isStreaming: liveIsStreaming,
  isProcessing: liveIsProcessing,
  capturedCount: liveCapturedCount,
  batchCount: liveBatchCount,
  lastResult: liveLastResult,
  lastError: liveLastError,
  history: liveHistory,
  start: liveStart,
  stop: liveStop,
  flush: liveFlush,
} = liveAll;

const liveVideoEl = ref<HTMLVideoElement | null>(null);

// === 切换到 live 模式时自动启动 / 切回 photo 时停止 ===
watch(mode, async (v) => {
  if (v === 'live') {
    await nextTick();
    try {
      await liveStart(liveVideoEl.value);
    } catch {
      // 权限拒绝时回到拍照模式
      mode.value = 'photo';
    }
  } else {
    liveStop();
  }
});

async function handleConfirm(blob: Blob) {
  await submit(blob);
}

function handleReplay(text: string) {
  if (text) tts.speak(text);
}

const streamingStatus = computed(() => {
  if (liveLastError.value) return 'error';
  if (liveIsProcessing.value) return 'processing';
  if (liveIsStreaming.value) return 'streaming';
  return 'idle';
});

const statusLabel = computed(() => ({
  idle: '未启动',
  streaming: '采集中',
  processing: '推理中',
  error: '出错',
}[streamingStatus.value]));

// 危险结果数量（视障用户高优提示）
const dangerCount = computed(
  () => liveHistory.value.filter((h) => h.priority === 'high').length,
);

// 卸载前主动 flush 一次（尽量保留最后一批识别结果到历史库）
onBeforeUnmount(async () => {
  try {
    await liveFlush();
  } catch {
    // ignore
  }
});

// 为键盘可达性提供：模式切换可用 Space 触发
function handleModeKey(e: KeyboardEvent) {
  if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault();
    mode.value = mode.value === 'live' ? 'photo' : 'live';
  }
}
</script>

<template>
  <div class="travel-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">出行感知</h1>
      <p class="page-desc">
        对准前方环境，识别障碍、行人、红绿灯、台阶等
      </p>

      <!-- 模式切换（segmented control） -->
      <div
        class="mode-tabs"
        role="tablist"
        aria-label="识别模式"
      >
        <button
          class="mode-tab"
          :class="{ active: mode === 'live' }"
          role="tab"
          :aria-selected="mode === 'live'"
          tabindex="0"
          @click="mode = 'live'"
          @keydown="handleModeKey"
        >
          🎥 实时模式
        </button>
        <button
          class="mode-tab"
          :class="{ active: mode === 'photo' }"
          role="tab"
          :aria-selected="mode === 'photo'"
          tabindex="0"
          @click="mode = 'photo'"
          @keydown="handleModeKey"
        >
          📷 拍照模式
        </button>
      </div>
    </header>

    <div class="biz-layout" :class="{ mobile: isMobile }">
      <!-- 左侧：相机/视频预览 -->
      <section class="biz-camera" aria-label="相机区域">
        <!-- 实时模式：WebRTC 视频预览 + 状态/统计 -->
        <template v-if="mode === 'live'">
          <div class="live-panel">
            <div class="live-preview">
              <video
                v-show="liveIsStreaming"
                ref="liveVideoEl"
                class="live-video"
                autoplay
                muted
                playsinline
                aria-label="WebRTC 实时摄像头预览"
              />
              <div v-if="!liveIsStreaming" class="live-placeholder">
                <el-icon :size="48" aria-hidden="true"><VideoCamera /></el-icon>
                <p>正在请求摄像头权限…</p>
              </div>
              <div v-else class="live-overlay" aria-hidden="true">
                <span class="live-dot" />
                <span>REC · 已采集 {{ liveCapturedCount }} 帧</span>
              </div>
            </div>

            <div class="live-status" role="status" aria-live="polite">
              <div class="status-row">
                <span class="status-tag" :data-status="streamingStatus">
                  {{ statusLabel }}
                </span>
                <span class="stat">
                  批次 {{ liveBatchCount }}
                </span>
              </div>
              <div
                v-if="liveLastError"
                class="live-error"
                role="alert"
              >
                ⚠ {{ liveLastError }}
              </div>
              <div class="live-actions">
                <button
                  v-if="liveIsStreaming"
                  class="live-btn danger"
                  aria-label="停止实时识别"
                  @click="liveStop()"
                >
                  ⏹ 停止
                </button>
                <button
                  v-else
                  class="live-btn primary"
                  aria-label="启动实时识别"
                  @click="liveStart(liveVideoEl)"
                >
                  ▶ 启动
                </button>
                <button
                  class="live-btn"
                  aria-label="立即识别当前帧"
                  :disabled="!liveIsStreaming || liveIsProcessing"
                  @click="liveFlush()"
                >
                  ⚡ 立即识别
                </button>
              </div>
              <p class="live-hint">
                💡 摄像头每 1 秒抓一帧，每 4 帧为一批发往后端，多帧时序理解更准。
                命中"台阶/车辆/坑洞"等危险词会自动优先播报。
              </p>
            </div>
          </div>
        </template>

        <!-- 拍照模式：原有 CameraCapture -->
        <CameraCapture
          v-else
          :auto-start="true"
          facing-mode="environment"
          @confirm="handleConfirm"
        />
      </section>

      <!-- 右侧：识别结果 -->
      <section class="biz-result" aria-label="识别结果">
        <!-- 实时模式结果展示 -->
        <template v-if="mode === 'live'">
          <div class="live-result">
            <header class="result-header-bar">
              <h2 class="result-title">实时感知</h2>
              <span
                v-if="dangerCount > 0"
                class="danger-badge"
                role="alert"
                aria-live="assertive"
              >
                ⚠️ {{ dangerCount }} 条危险事件
              </span>
            </header>

            <!-- 最新结果 -->
            <div
              v-if="liveLastResult"
              class="latest-card"
              :class="{ danger: liveLastResult.priority === 'high' }"
              :aria-live="liveLastResult.priority === 'high' ? 'assertive' : 'polite'"
            >
              <p class="latest-text">{{ liveLastResult.content }}</p>
              <div class="latest-meta">
                <span>
                  {{ liveLastResult.framesUsed ?? 4 }} 帧
                  · {{ liveLastResult.latencyMs ?? '—' }} ms
                </span>
                <button
                  class="replay-btn"
                  aria-label="重听最新结果"
                  @click="handleReplay(liveLastResult.content)"
                >
                  🔊 重听
                </button>
              </div>
            </div>

            <!-- 空状态 -->
            <EmptyState
              v-else-if="!liveIsProcessing"
              title="等待实时识别结果"
              description="启动实时模式后会自动采集画面"
              icon="View"
            />

            <!-- 历史时间线 -->
            <div v-if="liveHistory.length > 0" class="history-timeline">
              <h3 class="timeline-title">最近 {{ liveHistory.length }} 批</h3>
              <ul class="timeline-list">
                <li
                  v-for="(h, idx) in liveHistory"
                  :key="String(h.id ?? `${h.createdAt}-${idx}`)"
                  :class="{ danger: h.priority === 'high' }"
                >
                  <span class="timeline-marker" aria-hidden="true">
                    {{ h.priority === 'high' ? '⚠️' : '·' }}
                  </span>
                  <span class="timeline-text">{{ h.content }}</span>
                  <button
                    class="timeline-replay"
                    aria-label="重听这条结果"
                    @click="handleReplay(h.content)"
                  >
                    🔊
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </template>

        <!-- 拍照模式结果展示 -->
        <template v-else>
          <ResultDisplay
            title="出行场景识别"
            :content="result?.content"
            :audio-url="result?.audioUrl"
            :loading="loading"
            :empty="!result"
          />
          <EmptyState
            v-if="!loading && !result"
            title="请拍摄前方画面"
            description="点击底部拍照按钮，或直接选择照片"
            icon="Camera"
          />
        </template>
      </section>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use "@/assets/styles/variables.scss" as *;

.travel-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}
.page-header {
  text-align: center;
}
.page-title {
  font-size: 24px;
  color: $text-main;
  margin: 0 0 4px;
}
.page-desc {
  color: $text-secondary;
  font-size: 14px;
  margin: 0 0 12px;
}

/* === 模式切换 Tabs === */
.mode-tabs {
  display: inline-flex;
  gap: 6px;
  background: $bg-elevated;
  border-radius: 999px;
  padding: 4px;
  box-shadow: $shadow-inset-sm;
}
.mode-tab {
  border: 0;
  background: transparent;
  padding: 8px 18px;
  border-radius: 999px;
  color: $text-secondary;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: $transition-base;
  &:hover { color: $text-main; }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
  &.active {
    background: $bg-main;
    color: $accent;
    box-shadow: $shadow-sm;
    font-weight: 600;
  }
}

/* === 左右两栏布局 === */
.biz-layout {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 16px;
  flex: 1;
  min-height: 480px;
}
.biz-layout.mobile {
  grid-template-columns: 1fr;
}
.biz-camera, .biz-result {
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

/* === 实时面板 === */
.live-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 16px;
  height: 100%;
}
.live-preview {
  position: relative;
  flex: 1;
  min-height: 280px;
  background: #111;
  border-radius: $radius-md;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.live-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.live-placeholder {
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  p { margin: 0; font-size: 14px; }
}
.live-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  border-radius: 999px;
  font-weight: 600;
}
.live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff5252;
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50%      { opacity: 1; }
}
.live-status {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: $bg-elevated;
  border-radius: $radius-md;
  box-shadow: $shadow-inset-sm;
}
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.06);
  color: $text-secondary;
  &[data-status="streaming"]  { background: #e8f5e9; color: #2e7d32; }
  &[data-status="processing"] { background: #fff8e1; color: #ef6c00; }
  &[data-status="error"]      { background: #ffebee; color: #c62828; }
}
.stat {
  font-size: 12px;
  color: $text-muted;
  font-family: monospace;
}
.live-error {
  color: $color-danger;
  font-size: 13px;
}
.live-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.live-btn {
  height: 40px;
  padding: 0 14px;
  background: $bg-main;
  color: $text-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: $transition-base;
  &:hover:not(:disabled) { box-shadow: $shadow-md; }
  &:active:not(:disabled), &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &.primary { background: $accent; color: #fff; }
  &.danger  { background: $color-danger; color: #fff; }
}
.live-hint {
  margin: 0;
  color: $text-muted;
  font-size: 12px;
  line-height: 1.6;
}

/* === 实时模式结果 === */
.live-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}
.result-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.result-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: $text-main;
}
.danger-badge {
  background: $color-danger;
  color: #fff;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.latest-card {
  background: $bg-elevated;
  border-radius: $radius-md;
  padding: 16px 18px;
  box-shadow: $shadow-inset-sm;
  &.danger {
    box-shadow: $shadow-inset-sm, 0 0 0 2px $color-danger;
    animation: dangerPulse 1.6s ease-in-out infinite;
  }
}
@keyframes dangerPulse {
  0%, 100% { box-shadow: $shadow-inset-sm, 0 0 0 2px $color-danger; }
  50%      { box-shadow: $shadow-inset-sm, 0 0 0 4px $color-danger; }
}
.latest-text {
  font-size: 20px;
  line-height: 1.6;
  color: $text-main;
  font-weight: 500;
  margin: 0 0 10px;
}
.latest-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: $text-muted;
  font-size: 12px;
}
.replay-btn {
  background: $bg-main;
  border: 0;
  padding: 4px 10px;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: 12px;
  color: $text-main;
  box-shadow: $shadow-sm;
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}

/* === 历史时间线 === */
.history-timeline {
  margin-top: auto;
  padding-top: 12px;
}
.timeline-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: $text-secondary;
}
.timeline-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 220px;
  overflow-y: auto;
}
.timeline-list li {
  display: grid;
  grid-template-columns: 24px 1fr 32px;
  align-items: start;
  gap: 8px;
  padding: 8px 12px;
  background: $bg-elevated;
  border-radius: $radius-sm;
  font-size: 14px;
  color: $text-main;
  &.danger {
    background: #fff3e0;
    color: #bf360c;
    font-weight: 500;
  }
}
.timeline-marker { font-weight: 700; }
.timeline-text {
  line-height: 1.5;
  word-break: break-word;
}
.timeline-replay {
  background: $bg-main;
  border: 0;
  border-radius: $radius-sm;
  cursor: pointer;
  width: 28px;
  height: 28px;
  font-size: 12px;
  box-shadow: $shadow-sm;
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
</style>
