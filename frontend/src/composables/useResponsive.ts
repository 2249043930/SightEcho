/**
 * composables/useResponsive.ts
 * 实时响应窗口变化，返回当前设备类型
 * 性能：使用 useDebounceFn 包裹 resize 监听，200ms 节流
 * SSR 安全：onMounted 后才挂载 window 监听
 */
import { ref, computed, onMounted, onBeforeUnmount, readonly } from 'vue';
import { useDebounceFn } from '@vueuse/core';

export type DeviceType = 'mobile' | 'tablet' | 'laptop' | 'desktop';

const BREAKPOINTS = {
  mobile: 768,
  tablet: 992,
  laptop: 1200,
  desktop: 1920,
} as const;

export function useResponsive() {
  const width = ref(typeof window !== 'undefined' ? window.innerWidth : 1920);
  const height = ref(typeof window !== 'undefined' ? window.innerHeight : 1080);

  const update = useDebounceFn(() => {
    width.value = window.innerWidth;
    height.value = window.innerHeight;
  }, 200);

  const isMobile = computed(() => width.value < BREAKPOINTS.mobile);
  const isTablet = computed(
    () => width.value >= BREAKPOINTS.mobile && width.value < BREAKPOINTS.tablet,
  );
  const isLaptop = computed(
    () => width.value >= BREAKPOINTS.tablet && width.value < BREAKPOINTS.desktop,
  );
  const isDesktop = computed(() => width.value >= BREAKPOINTS.desktop);

  const device = computed<DeviceType>(() => {
    if (isMobile.value) return 'mobile';
    if (isTablet.value) return 'tablet';
    if (isLaptop.value) return 'laptop';
    return 'desktop';
  });

  onMounted(() => {
    if (typeof window === 'undefined') return;
    width.value = window.innerWidth;
    height.value = window.innerHeight;
    window.addEventListener('resize', update);
    window.addEventListener('orientationchange', update);
  });

  onBeforeUnmount(() => {
    if (typeof window === 'undefined') return;
    window.removeEventListener('resize', update);
    window.removeEventListener('orientationchange', update);
  });

  return {
    width: readonly(width),
    height: readonly(height),
    isMobile,
    isTablet,
    isLaptop,
    isDesktop,
    device,
  };
}
