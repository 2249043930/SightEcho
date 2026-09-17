<script setup lang="ts">
/**
 * components/business/CameraCapture.vue
 * 相机拍摄 / 视频流
 */
import { ref, onBeforeUnmount, onMounted, computed } from 'vue';
import { useCamera } from '@/composables/useCamera';
import { useResponsive } from '@/composables/useResponsive';

const props = withDefaults(
  defineProps<{
    facingMode?: 'user' | 'environment';
    autoStart?: boolean;
  }>(),
  { facingMode: 'environment', autoStart: false },
);

const emit = defineEmits<{
  (e: 'capture', blob: Blob): void;
  (e: 'cancel'): void;
  (e: 'confirm', blob: Blob): void;
}>();

const { isMobile } = useResponsive();
const videoRef = ref<HTMLVideoElement | null>(null);
const previewUrl = ref<string | null>(null);
const { stream, isActive, error, start, stop, captureFrame } = useCamera({
  facingMode: props.facingMode,
});

const captured = computed(() => !!previewUrl.value);

async function handleStart() {
  if (videoRef.value) videoRef.value.setAttribute('data-camera-target', '');
  await start(videoRef.value);
}

async function handleCapture() {
  try {
    const blob = await captureFrame(0.9);
    previewUrl.value = URL.createObjectURL(blob);
    emit('capture', blob);
  } catch (e) {
    console.error('拍照失败：', e);
  }
}

function handleRetake() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }
}

function handleConfirm() {
  captureFrame(0.9).then((blob) => {
    emit('confirm', blob);
  });
}

function handleCancel() {
  stop();
  handleRetake();
  emit('cancel');
}

function switchCamera() {
  stop();
  // 简单切换：父组件需通过重新传入 facingMode 实现
}

onMounted(() => {
  if (props.autoStart) handleStart();
});

onBeforeUnmount(() => {
  stop();
  handleRetake();
});
</script>

<template>
  <div class="camera-capture" :class="{ mobile: isMobile }">
    <div class="camera-preview">
      <video
        v-if="!previewUrl"
        ref="videoRef"
        class="camera-video"
        data-camera-target
        autoplay
        muted
        playsinline
        aria-label="相机预览"
      />
      <img
        v-else
        :src="previewUrl"
        class="camera-photo"
        alt="拍摄预览"
      />
      <div v-if="error" class="camera-error" role="alert">
        <el-icon :size="32"><WarningFilled /></el-icon>
        <p>{{ error }}</p>
        <button class="retry-btn" @click="handleStart">重试</button>
      </div>
    </div>

    <div class="camera-controls" role="toolbar" aria-label="相机控制">
      <button
        v-if="!previewUrl"
        class="ctrl-btn"
        :disabled="!isActive"
        aria-label="切换摄像头"
        @click="switchCamera"
      >
        <el-icon :size="24"><RefreshRight /></el-icon>
        <span>切换</span>
      </button>
      <button
        v-if="!previewUrl"
        class="ctrl-btn primary"
        :disabled="!isActive"
        aria-label="拍照"
        @click="handleCapture"
      >
        <span class="shutter" />
      </button>
      <button
        v-if="!previewUrl"
        class="ctrl-btn"
        aria-label="取消"
        @click="handleCancel"
      >
        <el-icon :size="24"><Close /></el-icon>
        <span>取消</span>
      </button>

      <template v-else>
        <button class="ctrl-btn" aria-label="重拍" @click="handleRetake">
          <el-icon :size="24"><RefreshLeft /></el-icon>
          <span>重拍</span>
        </button>
        <button class="ctrl-btn primary" aria-label="确认" @click="handleConfirm">
          <el-icon :size="24"><Check /></el-icon>
          <span>确认</span>
        </button>
        <button class="ctrl-btn" aria-label="取消" @click="handleCancel">
          <el-icon :size="24"><Close /></el-icon>
          <span>取消</span>
        </button>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.camera-capture {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 16px;
  height: 100%;
}
@include mobile {
  .camera-capture { padding: 0; box-shadow: none; background: $text-main; }
}
.camera-preview {
  position: relative;
  flex: 1;
  min-height: 240px;
  background: $text-main;
  border-radius: $radius-md;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.camera-video, .camera-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.camera-error {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 16px;
}
.retry-btn {
  height: 44px;
  padding: 0 20px;
  background: $accent;
  color: #fff;
  border: 0;
  border-radius: $radius-md;
  cursor: pointer;
  font-weight: 600;
}
.camera-controls {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 12px;
  padding: 12px;
}
@include mobile {
  .camera-controls {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0, 0, 0, 0.6);
    padding: 16px;
    z-index: 50;
  }
}
.ctrl-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 64px;
  min-height: 64px;
  padding: 8px 12px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  color: $text-main;
  cursor: pointer;
  box-shadow: $shadow-sm;
  transition: $transition-base;
  font-size: 12px;
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  span { font-size: 12px; }
}
@include mobile {
  .ctrl-btn {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    box-shadow: none;
    &:active { background: rgba(255, 255, 255, 0.2); }
  }
}
.ctrl-btn.primary {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: $bg-main;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  span { font-size: 0; }
}
.shutter {
  display: block;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: $accent;
  box-shadow: inset 0 0 0 4px $bg-main;
}
</style>
