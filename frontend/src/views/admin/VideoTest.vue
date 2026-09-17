<script setup lang="ts">
/**
 * views/admin/VideoTest.vue
 * 视频流解析测试页面
 * 流程：输入 RTSP/RTMP/HTTP URL → 提交任务 → 轮询状态 / SSE 实时获取 → 展示识别结果
 */
import { ref, computed, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import {
  startVideoParse,
  getVideoTask,
  buildVideoStreamURL,
  type VideoFrame,
  type VideoScene,
} from '@/api/video';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();

// ----- 表单 -----
const form = ref({
  src: '',
  scene: 'travel' as VideoScene,
  fps: 1,
});
const submitting = ref(false);
const taskId = ref<string | null>(null);
const error = ref<string | null>(null);

// ----- 状态 -----
const taskStatus = ref<'idle' | 'pending' | 'running' | 'completed' | 'failed'>('idle');
const frames = ref<VideoFrame[]>([]);
const startedAt = ref<number | null>(null);
const finishedAt = ref<number | null>(null);
let pollTimer: number | null = null;
let eventSource: EventSource | null = null;

// ----- 快捷模板（视频源） -----
const quickSources = [
  { label: '本地摄像头（Windows）', value: '0' },
  { label: '公开测试流（Big Buck Bunny）', value: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4' },
  { label: 'RTSP 模板', value: 'rtsp://admin:admin@192.168.1.100:554/stream1' },
  { label: '本地 mp4（test.mp4）', value: 'test.mp4' },
];

// ----- 场景选项 -----
const sceneOptions: { value: VideoScene; label: string; icon: string; desc: string }[] = [
  { value: 'travel', label: '出行感知', icon: 'Promotion', desc: '识别台阶/车辆/障碍物，给出方位和距离' },
  { value: 'face', label: '人脸描述', icon: 'User', desc: '描述画面中人物（不识别身份）' },
  { value: 'ocr', label: '文档阅读', icon: 'Reading', desc: '识别图中文字（多帧合并）' },
  { value: 'product', label: '商品识别', icon: 'Goods', desc: '识别商品名称/类别/特征' },
  { value: 'currency', label: '货币识别', icon: 'Money', desc: '识别货币币种/面额' },
];

const canStart = computed(() => form.value.src.trim().length > 0 && !submitting.value);

const elapsed = computed(() => {
  if (!startedAt.value) return 0;
  const end = finishedAt.value || Date.now() / 1000;
  return Math.floor(end - startedAt.value);
});

const dangerFrames = computed(() =>
  frames.value.filter((f) => /⚠️|台阶|车辆|深坑|施工|电瓶车|积水|坑洼|消防|禁止|危险/.test(f.text))
);

const progressPercent = computed(() => {
  if (taskStatus.value === 'completed') return 100;
  if (taskStatus.value === 'failed') return 0;
  if (taskStatus.value === 'idle' || !startedAt.value) return 0;
  // 简单估算：每 4 秒出一帧
  return Math.min(95, Math.floor((elapsed.value / 4) * 100));
});

// ----- 操作 -----
async function handleStart() {
  if (!canStart.value) return;
  if (!userStore.token) {
    ElMessage.warning('请先登录');
    return;
  }
  error.value = null;
  submitting.value = true;
  frames.value = [];
  startedAt.value = null;
  finishedAt.value = null;
  taskStatus.value = 'pending';

  try {
    const resp = await startVideoParse({
      src: form.value.src.trim(),
      scene: form.value.scene,
      fps: Math.min(Math.max(form.value.fps, 1), 10),
    });
    taskId.value = resp.taskId;
    taskStatus.value = 'running';
    startedAt.value = Date.now() / 1000;
    ElMessage.success(`任务已启动：${resp.taskId.slice(0, 8)}...`);
    startPolling();
    startSSE();
  } catch (e: any) {
    error.value = e?.response?.data?.message || e?.message || '提交失败';
    taskStatus.value = 'failed';
    ElMessage.error(error.value!);
  } finally {
    submitting.value = false;
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = window.setInterval(async () => {
    if (!taskId.value || taskStatus.value === 'completed' || taskStatus.value === 'failed') return;
    try {
      const s = await getVideoTask(taskId.value);
      if (s.frames && s.frames.length > frames.value.length) {
        frames.value = s.frames;
      }
      if (s.status === 'completed' || s.status === 'failed') {
        taskStatus.value = s.status;
        finishedAt.value = s.finished_at || Date.now() / 1000;
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
      }
    } catch (e) {
      console.error('poll error', e);
    }
  }, 2000);
}

function startSSE() {
  if (!taskId.value) return;
  try {
    const url = buildVideoStreamURL(taskId.value);
    // EventSource 不支持自定义 Header，但我们的 token 通过 query 传
    const es = new EventSource(`${url}?token=${userStore.token}`);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.idx && data.text) {
          // 一帧结果
          if (!frames.value.find((f) => f.idx === data.idx)) {
            frames.value = [...frames.value, data];
          }
        } else if (data.status) {
          taskStatus.value = data.status;
          finishedAt.value = Date.now() / 1000;
        }
      } catch {}
    };
    es.onerror = () => {
      // 任务结束或网络错误 → 关闭
      es.close();
      if (taskStatus.value !== 'completed' && taskStatus.value !== 'failed') {
        // 拉一次最终状态
        pollOnce();
      }
    };
    eventSource = es;
  } catch (e) {
    console.error('SSE error', e);
  }
}

async function pollOnce() {
  if (!taskId.value) return;
  try {
    const s = await getVideoTask(taskId.value);
    frames.value = s.frames || [];
    if (s.status === 'completed' || s.status === 'failed') {
      taskStatus.value = s.status;
      finishedAt.value = s.finished_at || Date.now() / 1000;
    }
  } catch (e) {
    console.error(e);
  }
}

function handleReset() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  taskId.value = null;
  taskStatus.value = 'idle';
  frames.value = [];
  startedAt.value = null;
  finishedAt.value = null;
  error.value = null;
  form.value.src = '';
}

function useQuickSource(v: string) {
  form.value.src = v;
}

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('zh-CN', { hour12: false });
}

function playTTS(text: string) {
  if (!('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'zh-CN';
    u.rate = 1.0;
    window.speechSynthesis.speak(u);
  } catch (e) {
    console.warn('TTS 播放失败', e);
  }
}

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer);
  if (eventSource) eventSource.close();
});
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">🎥 视频流解析测试</h1>
        <p class="page-subtitle">
          提交 RTSP/RTMP/HTTP 视频源 → 业务侧抽帧 → 调用 JoyAI-VL 多图推理 → 实时返回识别结果
        </p>
      </div>
    </header>

    <!-- 表单卡片 -->
    <section class="card form-card">
      <h2 class="card-title">📋 任务配置</h2>
      <el-form :model="form" label-width="100px" label-position="top">
        <el-form-item label="视频流地址 (src)">
          <el-input
            v-model="form.src"
            placeholder="rtsp://user:pass@ip:port/stream 或 https://example.com/video.mp4 或 0（本地摄像头）"
            clearable
            :disabled="taskStatus === 'running' || taskStatus === 'pending'"
          />
        </el-form-item>
        <el-form-item label="快捷源">
          <div class="quick-sources">
            <el-tag
              v-for="s in quickSources"
              :key="s.value"
              class="quick-tag"
              :type="form.src === s.value ? 'primary' : 'info'"
              effect="plain"
              @click="useQuickSource(s.value)"
            >
              {{ s.label }}
            </el-tag>
          </div>
        </el-form-item>
        <div class="form-row">
          <el-form-item label="识别场景" class="row-item">
            <el-select v-model="form.scene" :disabled="taskStatus === 'running' || taskStatus === 'pending'">
              <el-option
                v-for="opt in sceneOptions"
                :key="opt.value"
                :value="opt.value"
                :label="opt.label"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="抽帧率 (fps)" class="row-item">
            <el-input-number
              v-model="form.fps"
              :min="1"
              :max="10"
              :step="1"
              :disabled="taskStatus === 'running' || taskStatus === 'pending'"
            />
          </el-form-item>
        </div>
        <div class="form-actions">
          <el-button
            v-if="taskStatus === 'idle' || taskStatus === 'failed' || taskStatus === 'completed'"
            type="primary"
            :loading="submitting"
            :disabled="!canStart"
            @click="handleStart"
          >
            ▶ 开始解析
          </el-button>
          <el-button v-else type="danger" @click="handleReset"> ⏹ 停止 </el-button>
          <el-button v-if="taskId" @click="handleReset"> 🔄 重置 </el-button>
        </div>
      </el-form>
    </section>

    <!-- 状态卡片 -->
    <section v-if="taskId" class="card status-card">
      <h2 class="card-title">
        📊 任务状态
        <el-tag :type="statusType" effect="dark" size="large" class="status-tag">
          {{ statusText }}
        </el-tag>
      </h2>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="Task ID">{{ taskId }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ elapsed }} 秒</el-descriptions-item>
        <el-descriptions-item label="已识别帧">{{ frames.length }} 帧</el-descriptions-item>
      </el-descriptions>
      <el-progress
        :percentage="progressPercent"
        :status="taskStatus === 'failed' ? 'exception' : taskStatus === 'completed' ? 'success' : ''"
        :stroke-width="14"
        class="progress-bar"
      />
      <p v-if="error" class="error-text">⚠ {{ error }}</p>
    </section>

    <!-- 结果区 -->
    <div v-if="frames.length > 0" class="result-grid">
      <!-- 危险事件高亮 -->
      <section v-if="dangerFrames.length > 0" class="card danger-card">
        <h2 class="card-title danger-title">
          ⚠️ 危险事件（自动检测）
          <el-badge :value="dangerFrames.length" type="danger" />
        </h2>
        <ul class="danger-list">
          <li
            v-for="f in dangerFrames"
            :key="`d-${f.idx}`"
            class="danger-item"
            @click="playTTS(f.text)"
            role="button"
            tabindex="0"
            @keydown.enter="playTTS(f.text)"
          >
            <span class="danger-idx">#{{ f.idx }}</span>
            <span class="danger-text">{{ f.text }}</span>
            <span class="danger-time">{{ formatTime(f.ts) }}</span>
          </li>
        </ul>
      </section>

      <!-- 全部识别结果 -->
      <section class="card frames-card">
        <h2 class="card-title">📋 全部识别结果（{{ frames.length }} 帧 / 批 {{ Math.ceil(frames.length / 4) }}）</h2>
        <el-table :data="frames" stripe max-height="500" class="frames-table">
          <el-table-column label="#" prop="idx" width="80" />
          <el-table-column label="时间" width="120">
            <template #default="{ row }">{{ formatTime(row.ts) }}</template>
          </el-table-column>
          <el-table-column label="使用帧数" width="80">
            <template #default="{ row }">{{ row.frames_used || 1 }}</template>
          </el-table-column>
          <el-table-column label="识别结果" prop="text">
            <template #default="{ row }">
              <span :class="{ 'text-danger': /⚠️/.test(row.text) }">{{ row.text }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" plain @click="playTTS(row.text)"> 🔊 </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <!-- 空状态 -->
    <section v-else-if="taskStatus === 'idle'" class="empty-state">
      <p>👆 在上方输入视频流地址，点「开始解析」即可</p>
      <p class="empty-tip">
        💡 提示：本页面同时支持 RTSP（监控/摄像头）、RTMP（直播流）、HTTPS（在线视频）、本地文件、本地摄像头
      </p>
    </section>
  </div>
</template>

<style lang="scss" scoped>
@use "@/assets/styles/variables.scss" as *;

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px 80px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.page-title {
  margin: 0;
  font-size: 28px;
  color: $text-main;
  font-weight: 700;
}
.page-subtitle {
  margin: 8px 0 0;
  color: $text-secondary;
  font-size: 14px;
}
.card {
  background: $bg-main;
  border-radius: $radius-xl;
  box-shadow: $shadow-md;
  padding: 24px 28px;
}
.card-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: $text-main;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}
.form-card :deep(.el-form-item) {
  margin-bottom: 16px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.row-item {
  margin-bottom: 0 !important;
}
.quick-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.quick-tag {
  cursor: pointer;
  transition: $transition-base;
  &:hover { transform: translateY(-1px); }
}
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
.status-card {
  .status-tag { margin-left: auto; }
  .progress-bar { margin-top: 16px; }
}
.error-text {
  color: $color-danger;
  margin-top: 12px;
  font-size: 14px;
}
.danger-card {
  border-left: 4px solid $color-danger;
  .danger-title { color: $color-danger; }
}
.danger-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.danger-item {
  display: grid;
  grid-template-columns: 50px 1fr 100px;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: $radius-md;
  cursor: pointer;
  transition: $transition-base;
  font-size: 15px;
  &:hover { box-shadow: $shadow-sm; }
  &:focus-visible {
    outline: 2px solid $color-danger;
    outline-offset: 2px;
  }
}
.danger-idx {
  color: $color-danger;
  font-weight: 700;
  font-family: monospace;
}
.danger-text {
  color: $text-main;
  font-weight: 500;
}
.danger-time {
  color: $text-muted;
  font-size: 12px;
  text-align: right;
}
.frames-card {
  .text-danger { color: $color-danger; font-weight: 600; }
}
.frames-table :deep(td) { vertical-align: middle; }
.result-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: $text-secondary;
  background: $bg-main;
  border-radius: $radius-xl;
  box-shadow: $shadow-inset-md;
  p { margin: 0; font-size: 16px; }
  .empty-tip { margin-top: 8px; font-size: 13px; color: $text-muted; }
}
</style>
