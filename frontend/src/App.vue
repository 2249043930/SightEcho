<script setup lang="ts">
import { onMounted } from 'vue';
import A11yAnnouncer from '@/components/common/A11yAnnouncer.vue';
import SkipLink from '@/components/common/SkipLink.vue';
import { useScreenReader } from '@/composables/useScreenReader';
import { useSettingsStore } from '@/stores/settings';
import { useDeviceStore } from '@/stores/device';

const { announce } = useScreenReader();
const settings = useSettingsStore();
const deviceStore = useDeviceStore();

onMounted(() => {
  // 绑定设备 store
  deviceStore.bind();
  // 应用全局字号
  document.documentElement.style.fontSize = settings.fontSize;
  // 启动播报
  setTimeout(() => announce('欢迎使用 SightEcho 昭视智伴', 'polite'), 300);
});
</script>

<template>
  <el-config-provider>
    <SkipLink />
    <A11yAnnouncer />
    <router-view v-slot="{ Component, route }">
      <transition name="fade" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </transition>
    </router-view>
  </el-config-provider>
</template>

<style>
#main-content {
  outline: none;
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
