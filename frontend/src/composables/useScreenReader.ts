/**
 * composables/useScreenReader.ts
 * 屏幕阅读器兼容：实时播报区域 + 路由切换播报
 */
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

export function useScreenReader() {
  const router = useRouter();
  let announcer: HTMLElement | null = null;

  function ensureAnnouncer() {
    if (!announcer) {
      announcer = document.getElementById('a11y-announcer');
    }
    return announcer;
  }

  /** 向实时播报区写一条文本，下次读屏会读出 */
  function announce(text: string, priority: 'polite' | 'assertive' = 'polite') {
    const el = ensureAnnouncer();
    if (!el) {
      // 兜底：动态创建
      const div = document.createElement('div');
      div.id = 'a11y-announcer';
      div.setAttribute('aria-live', 'assertive');
      div.setAttribute('aria-atomic', 'true');
      div.className = 'sr-only';
      document.body.appendChild(div);
      announcer = div;
    }
    el.setAttribute('aria-live', priority);
    // 先清空再赋值，确保读屏软件能感知到变化
    el.textContent = '';
    setTimeout(() => {
      if (announcer) announcer.textContent = text;
    }, 50);
  }

  onMounted(() => {
    router.afterEach((to) => {
      const title = (to.meta?.title as string) || '页面';
      announce(`已切换到 ${title}`, 'assertive');
    });
  });

  return { announce };
}
