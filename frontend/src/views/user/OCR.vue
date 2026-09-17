<script setup lang="ts">
/**
 * views/user/OCR.vue
 * 文档阅读：识别图片中的文字并朗读
 */
import CameraCapture from '@/components/business/CameraCapture.vue';
import ResultDisplay from '@/components/business/ResultDisplay.vue';
import { useResponsive } from '@/composables/useResponsive';
import { useRecognition } from '@/composables/useRecognition';

const { isMobile } = useResponsive();
const { loading, result, submit } = useRecognition('ocr');

async function handleConfirm(blob: Blob) {
  await submit(blob);
}
</script>

<template>
  <div class="ocr-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">文档阅读</h1>
      <p class="page-desc">对准文档、书本或任何文字，识别后将自动朗读</p>
    </header>
    <div class="biz-layout" :class="{ mobile: isMobile }">
      <section class="biz-camera" aria-label="相机区域">
        <CameraCapture :auto-start="true" @confirm="handleConfirm" />
      </section>
      <section class="biz-result" aria-label="识别结果">
        <ResultDisplay
          title="文字识别结果"
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
.ocr-page { display: flex; flex-direction: column; gap: 16px; height: 100%; }
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
