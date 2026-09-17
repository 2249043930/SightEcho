/**
 * composables/useLongPress.ts
 * 长按逻辑：支持鼠标 / 触摸 / 键盘 Space+Enter
 */
import { ref, onBeforeUnmount } from 'vue';

export interface UseLongPressOptions {
  /** 长按触发毫秒数 */
  duration?: number;
  /** 长按开始（按下瞬间） */
  onStart?: (e: Event) => void;
  /** 长按达到阈值 */
  onLongPress?: (e: Event) => void;
  /** 长按结束（松手 / 离开） */
  onEnd?: (e: Event) => void;
  /** 长按中途中断 */
  onCancel?: (e: Event) => void;
}

export function useLongPress(options: UseLongPressOptions = {}) {
  const { duration = 500 } = options;
  const pressing = ref(false);
  const triggered = ref(false);

  let timer: number | null = null;
  let startEv: Event | null = null;

  function clear() {
    if (timer) {
      window.clearTimeout(timer);
      timer = null;
    }
  }

  function start(e: Event) {
    if (pressing.value) return;
    pressing.value = true;
    triggered.value = false;
    startEv = e;
    options.onStart?.(e);
    clear();
    timer = window.setTimeout(() => {
      triggered.value = true;
      options.onLongPress?.(e);
    }, duration);
  }

  function end(e: Event) {
    if (!pressing.value) return;
    pressing.value = false;
    clear();
    if (triggered.value) {
      options.onEnd?.(e);
    } else {
      options.onCancel?.(e);
    }
    startEv = null;
  }

  function cancel(e: Event) {
    if (!pressing.value) return;
    pressing.value = false;
    triggered.value = false;
    clear();
    options.onCancel?.(e);
    startEv = null;
  }

  const events = {
    onMousedown: start,
    onMouseup: end,
    onMouseleave: cancel,
    onTouchstart: (e: TouchEvent) => start(e),
    onTouchend: (e: TouchEvent) => end(e),
    onTouchcancel: (e: TouchEvent) => cancel(e),
    onKeydown: (e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        start(e);
      }
      if (e.key === 'Escape') {
        cancel(e);
      }
    },
    onKeyup: (e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        end(e);
      }
    },
    onBlur: (e: FocusEvent) => cancel(e),
  };

  onBeforeUnmount(() => clear());

  return { pressing, triggered, events, start, end, cancel };
}
