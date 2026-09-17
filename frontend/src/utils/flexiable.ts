/**
 * utils/flexiable.ts
 * 动态设置 html 根字号（rem 适配）
 * 公式：baseSize * (Math.min(viewportWidth, 1920) / 1920)
 * 边界：最小 50px，最大 100px
 * 防抖：150ms
 */

const baseSize = 100; // 1rem = 100px（设计稿 1920 宽）
const minSize = 50;
const maxSize = 100;
const designWidth = 1920;

let timer: number | null = null;

function setRootFontSize(): void {
  const viewportWidth = Math.min(document.documentElement.clientWidth, designWidth);
  let fontSize = baseSize * (viewportWidth / designWidth);
  fontSize = Math.max(minSize, Math.min(maxSize, fontSize));
  document.documentElement.style.fontSize = `${fontSize}px`;
}

function debouncedResize(): void {
  if (timer) {
    window.clearTimeout(timer);
  }
  timer = window.setTimeout(() => {
    setRootFontSize();
  }, 150);
}

/**
 * 初始化 rem 适配
 * 在 main.ts 中调用一次即可
 */
export function initFlexible(): void {
  if (typeof window === 'undefined') return;
  setRootFontSize();
  window.addEventListener('resize', debouncedResize);
  window.addEventListener('orientationchange', debouncedResize);
  // 阻塞首屏渲染前提前设置
  document.addEventListener('DOMContentLoaded', setRootFontSize);
}

/**
 * px -> rem（按当前根字号计算）
 * @param px 像素值
 */
export function px2rem(px: number): string {
  const rootFontSize = parseFloat(document.documentElement.style.fontSize) || baseSize;
  return `${px / rootFontSize}rem`;
}

export default {
  initFlexible,
  px2rem,
};
