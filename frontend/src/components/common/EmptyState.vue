<script setup lang="ts">
/**
 * components/common/EmptyState.vue
 * 空状态占位
 */
withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    icon?: string;
  }>(),
  { title: '暂无数据', description: '当前没有可显示的内容', icon: 'Box' },
);
</script>

<template>
  <div
    class="empty-state"
    role="status"
    aria-live="polite"
  >
    <el-icon class="empty-icon" :size="64" aria-hidden="true">
      <component :is="icon" />
    </el-icon>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: $text-secondary;
}
.empty-icon {
  color: $text-muted;
  margin-bottom: 16px;
}
.empty-title {
  font-size: 18px;
  color: $text-main;
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 14px;
  color: $text-secondary;
  margin-bottom: 16px;
}
</style>
