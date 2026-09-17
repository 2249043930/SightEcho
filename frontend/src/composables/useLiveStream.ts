/**
 * composables/useLiveStream.ts
 *
 * 给 Travel.vue 等页面用：在浏览器里调用 WebRTC（getUserMedia）取摄像头，
 * 按节奏抓帧 → 压缩成 base64 → 攒够一批（默认 4 帧）→ 调用 /recognition/live。
 *
 * 设计要点：
 *  - "实时帧识别" 不取代拍照识别，是另一种工作模式：
 *      实时模式：摄像头持续 1s/帧 抓取，4 帧一批提交；
 *      拍照模式：用户手动拍一张提交。
 *  - 危险关键词命中时（priority=high）会自动 TTS 播报（useTTS）。
 *  - 状态/进度都暴露 ref，方便 v-model/UI 绑定。
 *  - 失败时降级到 Demo 结果（由后端自动处理），不打扰视障用户。
 */
import { ref, onBeforeUnmount } from 'vue';
import { recognizeLive, type RecognitionType, type LiveRecognitionResult } from '@/api/recognition';
import { useTTS } from '@/composables/useTTS';

export interface UseLiveStreamOptions {
  /** 业务场景，默认 travel */
  scene?: RecognitionType;
  /** 后置/前置摄像头，默认 environment（手机后置） */
  facingMode?: 'user' | 'environment';
  /** 每多少毫秒抓一帧，默认 1000ms */
  frameIntervalMs?: number;
  /** 每多少帧攒成一组提交，默认 4 帧一批 */
  batchSize?: number;
  /** 每帧最大边长（用于压缩），默认 480，节省带宽与 token */
  resizeMaxSide?: number;
  /** JPEG 压缩质量 0~1，默认 0.6 */
  quality?: number;
  /** 是否自动播报结果，默认 true */
  autoSpeak?: boolean;
  /** 是否只播报高优先级（危险），普通结果不念 */
  onlySpeakDanger?: boolean;
  /** 是否把识别结果落库到 rec_record，默认 true */
  saveRecord?: boolean;
}

export function useLiveStream(options: UseLiveStreamOptions = {}) {
  const {
    scene = 'travel',
    facingMode = 'environment',
    frameIntervalMs = 1000,
    batchSize = 4,
    resizeMaxSide = 480,
    quality = 0.6,
    autoSpeak = true,
    onlySpeakDanger = true,
    saveRecord = true,
  } = options;

  const tts = useTTS();

  // === 状态（全部 ref 暴露给 UI） ===
  const stream = ref<MediaStream | null>(null);
  const videoEl = ref<HTMLVideoElement | null>(null);
  const isStreaming = ref(false);
  const isProcessing = ref(false);       // 后端正在推理
  const lastResult = ref<LiveRecognitionResult | null>(null);
  const lastError = ref<string | null>(null);
  /** 最近一次推理的低优先级"普通"结果历史（最多保留 8 条） */
  const history = ref<LiveRecognitionResult[]>([]);
  /** 已抓帧计数（调试用） */
  const capturedCount = ref(0);
  /** 已提交批次数（调试用） */
  const batchCount = ref(0);

  let frameTimer: number | null = null;
  let buffer: string[] = [];

  /** 启动视频流 + 定时抓帧循环 */
  async function start(targetVideo?: HTMLVideoElement | null) {
    if (isStreaming.value) return;
    if (targetVideo) videoEl.value = targetVideo;

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('当前浏览器不支持 getUserMedia');
      }
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      stream.value = s;
      if (videoEl.value) {
        videoEl.value.srcObject = s;
        // .play() 在某些浏览器下会拒绝（autoplay policy），吞掉即可
        await videoEl.value.play().catch(() => undefined);
      }
      isStreaming.value = true;
      lastError.value = null;
      capturedCount.value = 0;
      batchCount.value = 0;
      buffer = [];

      // 启动抓帧循环
      frameTimer = window.setInterval(captureAndBuffer, frameIntervalMs);
    } catch (e: any) {
      lastError.value = e?.message || '启动摄像头失败';
      isStreaming.value = false;
      throw e;
    }
  }

  /** 停止视频流与定时器（幂等） */
  function stop() {
    if (frameTimer) {
      window.clearInterval(frameTimer);
      frameTimer = null;
    }
    stream.value?.getTracks().forEach((t) => t.stop());
    stream.value = null;
    if (videoEl.value) {
      videoEl.value.srcObject = null;
    }
    isStreaming.value = false;
    isProcessing.value = false;
    buffer = [];
  }

  /**
   * 内部：从 video 元素截一帧 → 缩放 → JPEG → base64，
   *        攒够 batchSize 后批量调用 /recognition/live。
   *        为了不阻塞抓帧节拍，推理异步触发（错误吞掉，下一批继续）。
   */
  async function captureAndBuffer() {
    const video = videoEl.value;
    if (!video || !video.videoWidth || !video.videoHeight) return;
    try {
      const b64 = await frameToJpegBase64(video, resizeMaxSide, quality);
      buffer.push(b64);
      capturedCount.value += 1;
      if (buffer.length >= batchSize) {
        const batch = buffer.slice(0, batchSize);
        buffer = buffer.slice(batchSize);
        // 异步触发，不要 await（保持抓帧节拍稳定）
        void submitBatch(batch).catch((e) => console.warn('submit batch failed', e));
      }
    } catch (e) {
      console.warn('抓帧失败', e);
    }
  }

  /** 把当前 buffer 强制刷一批（用于 onUnmounted / 手动 flush） */
  async function flush() {
    if (!buffer.length) return;
    const batch = buffer.slice();
    buffer = [];
    await submitBatch(batch);
  }

  /** 手动提交一组帧（暴露给业务组件，用于"立即识别"按钮） */
  async function submitBatch(images: string[]) {
    if (!images.length) return;
    isProcessing.value = true;
    try {
      const r = await recognizeLive({ scene, images, saveRecord });
      handleResult(r);
    } catch (e: any) {
      // 错误静默处理（前端不打扰用户），仅记录到 ref 供 UI 展示
      lastError.value = e?.message || '实时识别失败';
    } finally {
      isProcessing.value = false;
      batchCount.value += 1;
    }
  }

  /** 处理一条识别结果：写入历史 + 危险时 TTS */
  function handleResult(r: LiveRecognitionResult) {
    lastResult.value = r;
    history.value = [r, ...history.value].slice(0, 8);

    if (autoSpeak && r.content) {
      const isDanger = r.priority === 'high' || r.resultJson?.priority === 'high';
      if (!onlySpeakDanger || isDanger) {
        tts.speak(r.content);
      }
    }
  }

  /** 重置历史/计数（视频组件卸载时使用） */
  function reset() {
    history.value = [];
    lastResult.value = null;
    lastError.value = null;
    capturedCount.value = 0;
    batchCount.value = 0;
  }

  // === 卸载：自动 stop 释放 MediaStream ===
  onBeforeUnmount(() => {
    stop();
  });

  return {
    // 状态
    stream,
    isStreaming,
    isProcessing,
    lastResult,
    lastError,
    history,
    capturedCount,
    batchCount,
    // 操作
    start,
    stop,
    flush,
    reset,
    submitBatch,
  };
}

// ============================================================
// 工具函数：从 video 元素截当前帧 → resize → JPEG base64
// ============================================================

/**
 * 截取当前帧，缩放到 maxSide 以内，转 jpeg base64。
 * 与 useCamera.ts 里的 captureFrame 区别：这里少了 Promise 包装，更轻量。
 */
async function frameToJpegBase64(
  video: HTMLVideoElement,
  maxSide = 480,
  quality = 0.6,
): Promise<string> {
  const w0 = video.videoWidth;
  const h0 = video.videoHeight;
  if (!w0 || !h0) throw new Error('video 元素尚未就绪');

  let w = w0;
  let h = h0;
  if (Math.max(w, h) > maxSide) {
    if (w >= h) {
      h = Math.round((maxSide / w) * h);
      w = maxSide;
    } else {
      w = Math.round((maxSide / h) * w);
      h = maxSide;
    }
  }

  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D 上下文不可用');
  ctx.drawImage(video, 0, 0, w, h);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error('Canvas 转 Blob 失败'));
          return;
        }
        const reader = new FileReader();
        reader.onloadend = () => {
          const s = String(reader.result || '');
          // 去掉 "data:image/jpeg;base64," 前缀
          const idx = s.indexOf(',');
          resolve(idx >= 0 ? s.slice(idx + 1) : s);
        };
        reader.onerror = () => reject(new Error('读取 Blob 失败'));
        reader.readAsDataURL(blob);
      },
      'image/jpeg',
      quality,
    );
  });
}
