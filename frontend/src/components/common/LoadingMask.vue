<script setup lang="ts">
/**
 * components/common/LoadingMask.vue
 * 加载遮罩
 */
withDefaults(
  defineProps<{
    visible?: boolean;
    text?: string;
    fullscreen?: boolean;
  }>(),
  { visible: false, text: '正在加载…', fullscreen: false },
);
</script>

<template>
  <transition name="fade">
    <div
      v-if="visible"
      class="loading-mask"
      :class="{ 'is-fullscreen': fullscreen }"
      role="alert"
      aria-busy="true"
    >
      <div class="loading-box">
        <div class="loading-spinner" aria-hidden="true" />
        <p class="loading-text">{{ text }}</p>
        <span class="sr-only">{{ text }}</span>
      </div>
    </div>
  </transition>
</template>

<style lang="scss" scoped>
.loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(224, 229, 236, 0.7);
  backdrop-filter: blur(2px);
  z-index: 10;
  border-radius: inherit;
}
.loading-mask.is-fullscreen {
  position: fixed;
  inset: 0;
  border-radius: 0;
  z-index: 9999;
}
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 32px;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid $shadow-dark;
  border-top-color: $accent;
  animation: spin 0.8s linear infinite;
}
.loading-text {
  color: $text-main;
  font-size: 14px;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
