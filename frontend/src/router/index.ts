/**
 * router/index.ts
 * 路由表（含懒加载 + 权限守卫）
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useUserStore } from '@/stores/user';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/Login.vue'),
    meta: { title: '登录', public: true, layout: 'blank' },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    redirect: { name: 'Home' },
    children: [
      // 用户端
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/user/Home.vue'),
        meta: { title: '首页', icon: 'House' },
      },
      {
        path: 'travel',
        name: 'Travel',
        component: () => import('@/views/user/Travel.vue'),
        meta: { title: '出行感知', icon: 'Promotion' },
      },
      {
        path: 'ocr',
        name: 'OCR',
        component: () => import('@/views/user/OCR.vue'),
        meta: { title: '文档阅读', icon: 'Reading' },
      },
      {
        path: 'currency',
        name: 'Currency',
        component: () => import('@/views/user/Currency.vue'),
        meta: { title: '货币识别', icon: 'Money' },
      },
      {
        path: 'product',
        name: 'Product',
        component: () => import('@/views/user/Product.vue'),
        meta: { title: '商品识别', icon: 'Goods' },
      },
      {
        path: 'face',
        name: 'Face',
        component: () => import('@/views/user/Face.vue'),
        meta: { title: '人脸描述', icon: 'User' },
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/user/History.vue'),
        meta: { title: '历史记录', icon: 'Clock' },
      },
      {
        path: 'history/detail',
        name: 'HistoryDetail',
        component: () => import('@/views/user/HistoryDetail.vue'),
        meta: { title: '记录详情', icon: 'Clock' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/user/Settings.vue'),
        meta: { title: '设置', icon: 'Setting' },
      },
      // 管理端
      {
        path: 'admin/dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理控制台', icon: 'DataLine', admin: true },
      },
      {
        path: 'admin/prompts',
        name: 'AdminPrompts',
        component: () => import('@/views/admin/PromptManager.vue'),
        meta: { title: 'Prompt 管理', icon: 'EditPen', admin: true },
      },
      {
        path: 'admin/monitor',
        name: 'AdminMonitor',
        component: () => import('@/views/admin/Monitor.vue'),
        meta: { title: '接口监控', icon: 'Monitor', admin: true },
      },
      {
        path: 'admin/feedback',
        name: 'AdminFeedback',
        component: () => import('@/views/admin/Feedback.vue'),
        meta: { title: '用户反馈', icon: 'ChatLineRound', admin: true },
      },
      {
        path: 'admin/video-test',
        name: 'AdminVideoTest',
        component: () => import('@/views/admin/VideoTest.vue'),
        meta: { title: '视频流测试', icon: 'VideoCamera', admin: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/user/NotFound.vue'),
    meta: { title: '页面未找到', public: true, layout: 'blank' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore();

  // 设置页面标题
  const appTitle = 'SightEcho 昭视智伴';
  document.title = to.meta?.title ? `${to.meta.title} - ${appTitle}` : appTitle;

  // 公开页直接放行
  if (to.meta?.public) {
    // 已登录访问登录页时，重定向到首页
    if (to.name === 'Login' && userStore.isLoggedIn) {
      return next({ name: 'Home' });
    }
    return next();
  }

  // 需要登录
  if (!userStore.isLoggedIn) {
    return next({ name: 'Login', query: { redirect: to.fullPath } });
  }

  // 需要管理员
  if (to.meta?.admin && !userStore.isAdmin) {
    return next({ name: 'Home' });
  }

  next();
});

export default router;
