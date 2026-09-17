<script setup lang="ts">
/**
 * components/layout/AppSidebar.vue
 * 侧边栏：笔记本端 240px 固定 / 手机端抽屉
 */
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useResponsive } from '@/composables/useResponsive';

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>();

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const { isMobile } = useResponsive();

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
});

interface MenuGroup {
  title: string;
  items: { name: string; title: string; icon: string }[];
}

const groups = computed<MenuGroup[]>(() => {
  const user: MenuGroup = {
    title: '功能',
    items: [
      { name: 'Home', title: '首页', icon: 'House' },
      { name: 'Travel', title: '出行感知', icon: 'Promotion' },
      { name: 'OCR', title: '文档阅读', icon: 'Reading' },
      { name: 'Currency', title: '货币识别', icon: 'Money' },
      { name: 'Product', title: '商品识别', icon: 'Goods' },
      { name: 'Face', title: '人脸描述', icon: 'User' },
    ],
  };
  const profile: MenuGroup = {
    title: '我的',
    items: [
      { name: 'History', title: '历史记录', icon: 'Clock' },
      { name: 'Settings', title: '设置', icon: 'Setting' },
    ],
  };
  const groups: MenuGroup[] = [user, profile];
  if (userStore.isAdmin) {
    groups.push({
      title: '管理',
      items: [
        { name: 'AdminDashboard', title: '控制台', icon: 'DataLine' },
        { name: 'AdminPrompts', title: 'Prompt 管理', icon: 'EditPen' },
        { name: 'AdminMonitor', title: '接口监控', icon: 'Monitor' },
        { name: 'AdminFeedback', title: '用户反馈', icon: 'ChatLineRound' },
        { name: 'AdminVideoTest', title: '视频流测试', icon: 'VideoCamera' },
      ],
    });
  }
  return groups;
});

function go(name: string) {
  router.push({ name });
  if (isMobile.value) visible.value = false;
}
function close() {
  visible.value = false;
}
</script>

<template>
  <!-- 笔记本端：固定侧栏 -->
  <aside
    v-if="!isMobile"
    class="app-sidebar"
    role="navigation"
    aria-label="侧边导航"
  >
    <div class="sidebar-inner">
      <template v-for="group in groups" :key="group.title">
        <h3 class="sidebar-title">{{ group.title }}</h3>
        <ul class="sidebar-list" role="list">
          <li v-for="item in group.items" :key="item.name" role="listitem">
            <button
              :class="['sidebar-item', { active: route.name === item.name }]"
              :aria-current="route.name === item.name ? 'page' : undefined"
              @click="go(item.name)"
            >
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </button>
          </li>
        </ul>
      </template>
    </div>
  </aside>

  <!-- 手机端：抽屉 -->
  <el-drawer
    v-else
    v-model="visible"
    direction="ltr"
    :with-header="false"
    size="280px"
    :modal="true"
  >
    <div class="sidebar-inner">
      <button class="close-btn" aria-label="关闭菜单" @click="close">
        <el-icon :size="24"><Close /></el-icon>
      </button>
      <template v-for="group in groups" :key="group.title">
        <h3 class="sidebar-title">{{ group.title }}</h3>
        <ul class="sidebar-list" role="list">
          <li v-for="item in group.items" :key="item.name" role="listitem">
            <button
              :class="['sidebar-item', { active: route.name === item.name }]"
              :aria-current="route.name === item.name ? 'page' : undefined"
              @click="go(item.name)"
            >
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </button>
          </li>
        </ul>
      </template>
    </div>
  </el-drawer>
</template>

<style lang="scss" scoped>
.app-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: $bg-main;
  box-shadow: $shadow-sm;
  height: calc(100vh - 72px);
  position: sticky;
  top: 72px;
  overflow-y: auto;
}
.sidebar-inner {
  padding: 16px 12px;
}
.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  color: $text-muted;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 12px 12px 8px;
  margin: 0;
}
.sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 48px;
  padding: 0 16px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  color: $text-main;
  font-size: 15px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-sm; }
  &.active {
    background: $accent;
    color: #fff;
    box-shadow: $shadow-sm;
  }
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: -2px;
  }
}
.close-btn {
  width: 48px;
  height: 48px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
}
:deep(.el-drawer) {
  background: $bg-main !important;
  box-shadow: $shadow-lg !important;
}
:deep(.el-drawer__body) {
  padding: 0;
}
</style>
