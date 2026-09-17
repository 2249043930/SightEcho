<script setup lang="ts">
/**
 * components/common/A11yWrapper.vue
 * 无障碍包装组件：给区块提供 title / description 给读屏
 */
defineProps<{
  title: string;
  description?: string;
  as?: keyof HTMLElementTagNameMap;
}>();
</script>

<template>
  <section
    :aria-labelledby="`a11y-title-${$slots.default ? 'region' : 'region'}`"
    :aria-describedby="description ? 'a11y-desc-region' : undefined"
    role="region"
  >
    <h2 class="sr-only">{{ title }}</h2>
    <p v-if="description" id="a11y-desc-region" class="sr-only">{{ description }}</p>
    <slot />
  </section>
</template>
