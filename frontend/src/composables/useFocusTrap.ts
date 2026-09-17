/**
 * composables/useFocusTrap.ts
 * 模态框 / 抽屉打开时锁焦点，Esc 关闭
 * 基于 focus-trap 库
 */
import { onBeforeUnmount, watch, type Ref } from 'vue';
import { createFocusTrap, type FocusTrap } from 'focus-trap';

export interface UseFocusTrapOptions {
  immediate?: boolean;
  escapeDeactivates?: boolean;
  returnFocusOnDeactivate?: boolean;
  onActivate?: () => void;
  onDeactivate?: () => void;
}

export function useFocusTrap(
  containerRef: Ref<HTMLElement | null | undefined>,
  options: UseFocusTrapOptions = {},
) {
  let trap: FocusTrap | null = null;
  const {
    immediate = true,
    escapeDeactivates = true,
    returnFocusOnDeactivate = true,
    onActivate,
    onDeactivate,
  } = options;

  function activate() {
    if (!containerRef.value) return;
    if (trap) return;
    trap = createFocusTrap(containerRef.value, {
      escapeDeactivates,
      returnFocusOnDeactivate,
      onActivate,
      onDeactivate,
    });
    try {
      trap.activate();
    } catch (e) {
      console.warn('焦点陷阱激活失败：', e);
    }
  }

  function deactivate() {
    if (trap) {
      try {
        trap.deactivate();
      } catch (e) {
        console.warn('焦点陷阱关闭失败：', e);
      }
      trap = null;
    }
  }

  watch(
    containerRef,
    (el) => {
      if (el && immediate) {
        activate();
      } else if (!el) {
        deactivate();
      }
    },
    { immediate: true },
  );

  onBeforeUnmount(deactivate);

  return { activate, deactivate };
}
