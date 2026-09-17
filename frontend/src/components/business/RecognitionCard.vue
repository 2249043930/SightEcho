<script setup lang="ts">
/**
 * components/business/RecognitionCard.vue
 * 业务功能卡片（首页入口）
 */
import { ref } from 'vue';
import { useTTS } from '@/composables/useTTS';
import { useRouter } from 'vue-router';

const props = defineProps<{
  title: string;
  description: string;
  icon: string;
  routeName: string;
  shortcut?: string;
}>();

const router = useRouter();
const { speak, isSpeaking } = useTTS();
const hovering = ref(false);

function handleEnter() {
  hovering.value = true;
  if (!isSpeaking.value) {
    speak(`${props.title}：${props.description}`);
  }
}

function handleLeave() {
  hovering.value = false;
}

function handleClick() {
  router.push({ name: props.routeName });
}

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    handleClick();
  }
}
</script>

<template>
  <article
    class="recognition-card"
    :class="{ active: hovering }"
    role="link"
    :aria-label="`${title}：${description}${shortcut ? `，快捷键 ${shortcut}` : ''}`"
    tabindex="0"
    @click="handleClick"
    @keydown="handleKey"
    @mouseenter="handleEnter"
    @mouseleave="handleLeave"
    @focus="handleEnter"
    @blur="handleLeave"
  >
    <div class="card-icon" aria-hidden="true">
      <el-icon :size="40">
        <component :is="icon" />
      </el-icon>
    </div>
    <h3 class="card-title">{{ title }}</h3>
    <p class="card-desc">{{ description }}</p>
    <span v-if="shortcut" class="card-shortcut" aria-hidden="true">{{ shortcut }}</span>
  </article>
</template>

<style lang="scss" scoped>
.recognition-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  padding: 32px 20px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  cursor: pointer;
  transition: $transition-base;
  min-height: 200px;
  &:hover, &.active {
    box-shadow: $shadow-sm;
  }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.card-icon {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  border-radius: 50%;
  box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
  color: $accent;
}
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: $text-main;
  margin: 0;
}
.card-desc {
  font-size: 14px;
  color: $text-secondary;
  margin: 0;
  line-height: 1.5;
}
.card-shortcut {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $accent;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}
</style>
