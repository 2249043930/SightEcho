<script setup lang="ts">
/**
 * views/user/Face.vue
 * 人脸描述
 */
import CameraCapture from '@/components/business/CameraCapture.vue';
import ResultDisplay from '@/components/business/ResultDisplay.vue';
import { useResponsive } from '@/composables/useResponsive';
import { useRecognition } from '@/composables/useRecognition';

const { isMobile } = useResponsive();
const { loading, result, submit } = useRecognition('face');

async function handleConfirm(blob: Blob) {
  await submit(blob);
}
</script>

<template>
  <div class="face-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">人脸描述</h1>
      <p class="page-desc">对准人脸，将描述性别、年龄、表情与服饰</p>
    </header>
    <div class="biz-layout" :class="{ mobile: isMobile }">
      <section class="biz-camera" aria-label="相机区域">
        <CameraCapture :auto-start="true" facing-mode="user" @confirm="handleConfirm" />
      </section>
      <section class="biz-result" aria-label="识别结果">
        <ResultDisplay
          title="人脸描述"
          :content="result?.content"
          :audio-url="result?.audioUrl"
          :loading="loading"
          :empty="!result"
        />
      </section>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.face-page { display: flex; flex-direction: column; gap: 16px; height: 100%; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.biz-layout {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 16px;
  flex: 1;
  min-height: 480px;
}
.biz-layout.mobile { grid-template-columns: 1fr; }
.biz-camera, .biz-result { min-height: 400px; display: flex; flex-direction: column; }
</style>
