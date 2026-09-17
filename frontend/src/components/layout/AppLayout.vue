<script setup lang="ts">
/**
 * components/layout/AppLayout.vue
 * 整体布局容器：笔记本（Header + Sidebar + Main）/ 手机（Header + Main + 抽屉）
 */
import { ref } from 'vue';
import AppHeader from './AppHeader.vue';
import AppSidebar from './AppSidebar.vue';
import { useResponsive } from '@/composables/useResponsive';

const sidebarOpen = ref(false);
const { isMobile } = useResponsive();
</script>

<template>
  <div class="app-layout">
    <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    <div class="app-body">
      <AppSidebar v-if="!isMobile" />
      <AppSidebar v-else v-model="sidebarOpen" />
      <main id="main-content" class="app-main" tabindex="-1" role="main">
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-main;
}
.app-body {
  flex: 1;
  display: flex;
  min-height: 0;
}
.app-main {
  flex: 1;
  padding: 24px;
  overflow-x: hidden;
  outline: none;
  min-width: 0;
}
@include mobile {
  .app-main { padding: 16px 12px; }
}
.page-enter-active,
.page-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
}
</style>
