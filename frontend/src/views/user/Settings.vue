<script setup lang="ts">
/**
 * views/user/Settings.vue
 * 用户设置：语速、音量、唤醒、自动播报、字号档位
 * 笔记本：表单居中 max-width 720px；手机：单列全宽
 */
import { watch } from 'vue';
import { useSettingsStore } from '@/stores/settings';
import { useResponsive } from '@/composables/useResponsive';
import { updateUserSettings } from '@/api/user';
import { ElMessage } from 'element-plus';

const settings = useSettingsStore();
const { isMobile } = useResponsive();

// 同步到后端（节流：500ms）
let syncTimer: number | null = null;
function debouncedSync() {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = window.setTimeout(async () => {
    try {
      await updateUserSettings({
        speed: settings.speed,
        volume: settings.volume,
        wakeEnabled: settings.wakeEnabled,
        autoAnnounce: settings.autoAnnounce,
        fontScale: settings.fontScale,
      });
    } catch (e) {
      console.warn('设置同步失败：', e);
    }
  }, 500);
}

watch(
  () => [settings.speed, settings.volume, settings.wakeEnabled, settings.autoAnnounce, settings.fontScale],
  () => {
    document.documentElement.style.fontSize = settings.fontSize;
    debouncedSync();
  },
  { deep: true },
);

function handleReset() {
  settings.reset();
  ElMessage.success('已恢复默认设置');
}
</script>

<template>
  <div class="settings-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-desc">个性化您的使用体验</p>
    </header>

    <section class="settings-form" role="form" aria-label="用户设置">
      <article class="setting-block">
        <h2 class="block-title">语音播报</h2>

        <div class="setting-row">
          <label for="speed" class="row-label">语速 <span class="value">{{ settings.speed.toFixed(1) }}x</span></label>
          <el-slider
            id="speed"
            v-model="settings.speed"
            :min="0.5"
            :max="2"
            :step="0.1"
            show-stops
            aria-label="语速"
          />
        </div>

        <div class="setting-row">
          <label for="volume" class="row-label">音量 <span class="value">{{ settings.volume }}%</span></label>
          <el-slider
            id="volume"
            v-model="settings.volume"
            :min="0"
            :max="100"
            :step="1"
            aria-label="音量"
          />
        </div>

        <div class="setting-row">
          <div class="row-text">
            <span class="row-label">自动播报</span>
            <span class="row-desc">识别完成后自动 TTS 朗读</span>
          </div>
          <el-switch v-model="settings.autoAnnounce" aria-label="自动播报开关" />
        </div>
      </article>

      <article class="setting-block">
        <h2 class="block-title">语音唤醒</h2>
        <div class="setting-row">
          <div class="row-text">
            <span class="row-label">启用「小昭小昭」唤醒</span>
            <span class="row-desc">说出唤醒词即可开启语音交互</span>
          </div>
          <el-switch v-model="settings.wakeEnabled" aria-label="语音唤醒开关" />
        </div>
      </article>

      <article class="setting-block">
        <h2 class="block-title">显示</h2>
        <div class="setting-row">
          <div class="row-text">
            <span class="row-label">字号档位</span>
            <span class="row-desc">小（14px）/ 中（16px）/ 大（20px）</span>
          </div>
          <el-radio-group v-model="settings.fontScale" aria-label="字号档位">
            <el-radio-button value="small">小</el-radio-button>
            <el-radio-button value="medium">中</el-radio-button>
            <el-radio-button value="large">大</el-radio-button>
          </el-radio-group>
        </div>
      </article>

      <div class="form-actions">
        <button class="action-btn primary" @click="handleReset">恢复默认</button>
      </div>
    </section>
  </div>
</template>

<style lang="scss" scoped>
.settings-page {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.settings-page.mobile {
  max-width: 100%;
}
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.settings-form { display: flex; flex-direction: column; gap: 20px; }
.setting-block {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.block-title {
  font-size: 18px;
  font-weight: 600;
  color: $text-main;
  margin: 0 0 4px;
}
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 56px;
  padding: 8px 0;
}
@include mobile { .setting-row { flex-direction: column; align-items: flex-start; } }
.row-text { display: flex; flex-direction: column; gap: 4px; }
.row-label { font-size: 16px; color: $text-main; font-weight: 500; }
.row-desc { font-size: 13px; color: $text-secondary; }
.value { color: $accent; font-weight: 600; }
.form-actions { display: flex; justify-content: center; padding-top: 8px; }
.action-btn {
  height: 48px;
  padding: 0 32px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: $transition-base;
  &.primary {
    background: $accent;
    color: #fff;
    box-shadow: $shadow-sm;
  }
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
:deep(.el-slider__runway) { background: $bg-elevated !important; }
:deep(.el-slider__bar) { background: $accent !important; }
:deep(.el-slider__button) { border-color: $accent !important; }
:deep(.el-radio-button__inner) {
  background: $bg-main !important;
  border-color: $shadow-dark !important;
  color: $text-main !important;
  box-shadow: $shadow-sm !important;
}
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: $accent !important;
  color: #fff !important;
  box-shadow: $shadow-inset-sm !important;
  border-color: $accent !important;
}
</style>
