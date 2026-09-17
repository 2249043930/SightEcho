/**
 * composables/useCamera.ts
 * 摄像头调用：拍照、视频流、帧捕获
 */
import { ref, onBeforeUnmount } from 'vue';

interface UseCameraOptions {
  facingMode?: 'user' | 'environment';
  width?: number;
  height?: number;
}

export function useCamera(options: UseCameraOptions = {}) {
  const { facingMode = 'environment', width = 1280, height = 720 } = options;

  const stream = ref<MediaStream | null>(null);
  const isActive = ref(false);
  const error = ref<string | null>(null);

  async function start(videoEl?: HTMLVideoElement | null) {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('当前浏览器不支持 getUserMedia');
      }
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: width }, height: { ideal: height } },
        audio: false,
      });
      stream.value = s;
      isActive.value = true;
      if (videoEl) {
        videoEl.srcObject = s;
        await videoEl.play().catch(() => undefined);
      }
    } catch (e: any) {
      error.value = e?.message || '摄像头启动失败';
      throw e;
    }
  }

  function stop() {
    stream.value?.getTracks().forEach((t) => t.stop());
    stream.value = null;
    isActive.value = false;
  }

  /**
   * 从视频流截取当前帧，返回 Blob（image/jpeg）
   */
  function captureFrame(quality = 0.85): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const video = document.querySelector('video[data-camera-target]') as HTMLVideoElement | null;
      if (!video) {
        reject(new Error('未找到视频元素（请加 data-camera-target 属性）'));
        return;
      }
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas 2D 上下文不可用'));
        return;
      }
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => {
          if (blob) resolve(blob);
          else reject(new Error('Canvas 转 Blob 失败'));
        },
        'image/jpeg',
        quality,
      );
    });
  }

  onBeforeUnmount(stop);

  return { stream, isActive, error, start, stop, captureFrame };
}
