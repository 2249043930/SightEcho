<script setup lang="ts">
/**
 * components/common/A11yAnnouncer.vue
 * 实时播报区：供屏幕阅读器读取的 aria-live 区域
 */
</script>

<template>
  <div
    id="a11y-announcer"
    aria-live="assertive"
    aria-atomic="true"
    class="sr-only"
  />
</template>
