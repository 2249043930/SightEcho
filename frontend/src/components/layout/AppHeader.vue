<script setup lang="ts">
/**
 * components/layout/AppHeader.vue
 * 顶部导航：笔记本端横排菜单 / 手机端汉堡按钮
 */
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useResponsive } from '@/composables/useResponsive';
import { ElMessageBox } from 'element-plus';
import { maskEmail } from '@/utils/format';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const { isMobile } = useResponsive();

const emit = defineEmits<{ (e: 'toggle-sidebar'): void }>();

const userMenuOpen = ref(false);

const menuItems = computed(() => {
  const items: { name: string; title: string; icon: string; admin?: boolean }[] = [
    { name: 'Home', title: '首页', icon: 'House' },
    { name: 'History', title: '历史', icon: 'Clock' },
    { name: 'Settings', title: '设置', icon: 'Setting' },
  ];
  if (userStore.isAdmin) {
    items.push({ name: 'AdminDashboard', title: '管理', icon: 'DataLine' });
  }
  return items;
});

const currentTitle = computed(() => (route.meta?.title as string) || 'SightEcho');

function go(name: string) {
  router.push({ name });
}
function handleUser() {
  userMenuOpen.value = !userMenuOpen.value;
}
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确认退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    });
    userStore.logout();
    router.push({ name: 'Login' });
  } catch {
    /* 取消 */
  }
}
</script>

<template>
  <header class="app-header" role="banner">
    <div class="header-left">
      <button
        v-if="isMobile"
        class="hamburger"
        aria-label="打开菜单"
        @click="emit('toggle-sidebar')"
      >
        <el-icon :size="24"><Menu /></el-icon>
      </button>
      <h1 class="brand" @click="go('Home')">
        <span class="brand-icon" aria-hidden="true">◉</span>
        <span class="brand-text">SightEcho</span>
        <span class="brand-sub">昭视智伴</span>
      </h1>
    </div>

    <nav v-if="!isMobile" class="header-menu" aria-label="主导航">
      <button
        v-for="item in menuItems"
        :key="item.name"
        :class="['menu-item', { active: route.name === item.name }]"
        :aria-current="route.name === item.name ? 'page' : undefined"
        @click="go(item.name)"
      >
        <el-icon :size="18"><component :is="item.icon" /></el-icon>
        <span>{{ item.title }}</span>
      </button>
    </nav>

    <div class="header-right">
      <span class="page-title" aria-live="polite">{{ currentTitle }}</span>
      <button
        class="user-btn"
        :aria-expanded="userMenuOpen"
        aria-haspopup="menu"
        :aria-label="`当前用户：${maskEmail(userStore.profile?.email || '')}，点击展开菜单`"
        @click="handleUser"
      >
        <el-avatar :size="40" :src="userStore.profile?.avatar">
          {{ userStore.profile?.nickname?.[0] || 'U' }}
        </el-avatar>
      </button>
      <transition name="dropdown">
        <ul v-if="userMenuOpen" class="user-menu" role="menu">
          <li role="none">
            <button role="menuitem" class="user-menu-item" @click="() => { go('Settings'); userMenuOpen = false; }">
              <el-icon><Setting /></el-icon> 设置
            </button>
          </li>
          <li role="none">
            <button role="menuitem" class="user-menu-item" @click="() => { go('History'); userMenuOpen = false; }">
              <el-icon><Clock /></el-icon> 历史记录
            </button>
          </li>
          <li role="none">
            <button role="menuitem" class="user-menu-item danger" @click="handleLogout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </button>
          </li>
        </ul>
      </transition>
    </div>
  </header>
</template>

<style lang="scss" scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: $bg-main;
  box-shadow: $shadow-sm;
  position: sticky;
  top: 0;
  z-index: 100;
  min-height: 72px;
}
@include mobile {
  .app-header { padding: 8px 12px; min-height: 60px; }
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.hamburger {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
  &:active, &:focus-visible {
    box-shadow: $shadow-inset-sm;
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: $text-main;
  cursor: pointer;
  user-select: none;
}
.brand-icon {
  color: $accent;
  font-size: 24px;
  line-height: 1;
}
.brand-text { color: $text-main; }
.brand-sub {
  color: $text-secondary;
  font-size: 14px;
  font-weight: 400;
  margin-left: 4px;
}
.header-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 48px;
  padding: 0 16px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  color: $text-main;
  font-size: 15px;
  font-weight: 500;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
  &.active {
    background: $accent;
    color: #fff;
    box-shadow: $shadow-sm;
  }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}
.page-title {
  font-size: 16px;
  color: $text-secondary;
  font-weight: 500;
}
@include mobile { .page-title { display: none; } }
.user-btn {
  width: 48px;
  height: 48px;
  background: $bg-main;
  border: 0;
  border-radius: 50%;
  box-shadow: $shadow-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: $transition-base;
  padding: 0;
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: 2px;
  }
}
.user-menu {
  position: absolute;
  top: 56px;
  right: 0;
  min-width: 180px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-md-lg;
  padding: 8px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.user-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: 44px;
  padding: 0 12px;
  background: transparent;
  border: 0;
  border-radius: $radius-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
  transition: $transition-fast;
  &:hover { background: $bg-elevated; }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: -2px;
  }
  &.danger { color: $color-danger; }
}
.dropdown-enter-active, .dropdown-leave-active {
  transition: opacity 200ms, transform 200ms;
}
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
