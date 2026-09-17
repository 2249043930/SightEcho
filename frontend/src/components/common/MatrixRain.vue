<script setup lang="ts">
/**
 * components/common/MatrixRain.vue
 * 《黑客帝国》风格绿色数字雨背景（用户偏好）
 * 纯 Canvas 实现，零依赖
 */
import { ref, onMounted, onBeforeUnmount } from 'vue';

const canvasRef = ref<HTMLCanvasElement | null>(null);
let rafId: number | null = null;

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
const FONT_SIZE = 16;
const GREEN_PRIMARY = '#00ff66';
const GREEN_TRAIL = 'rgba(0, 0, 0, 0.05)';

interface Drop {
  x: number;
  y: number;
  speed: number;
}
let drops: Drop[] = [];

function init() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const cols = Math.floor(canvas.width / FONT_SIZE);
    drops = new Array(cols).fill(0).map(() => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      speed: 0.5 + Math.random() * 1.5,
    }));
  };
  resize();
  window.addEventListener('resize', resize);

  function draw() {
    ctx!.fillStyle = GREEN_TRAIL;
    ctx!.fillRect(0, 0, canvas.width, canvas.height);
    ctx!.fillStyle = GREEN_PRIMARY;
    ctx!.font = `${FONT_SIZE}px monospace`;
    for (const drop of drops) {
      const ch = CHARS[Math.floor(Math.random() * CHARS.length)];
      ctx!.fillText(ch, drop.x, drop.y);
      drop.y += drop.speed * FONT_SIZE;
      if (drop.y > canvas.height && Math.random() > 0.975) {
        drop.y = -FONT_SIZE;
        drop.x = Math.floor(Math.random() * (canvas.width / FONT_SIZE)) * FONT_SIZE;
      }
    }
    rafId = requestAnimationFrame(draw);
  }
  draw();

  onBeforeUnmount(() => {
    if (rafId) cancelAnimationFrame(rafId);
    window.removeEventListener('resize', resize);
  });
}

onMounted(init);
</script>

<template>
  <canvas ref="canvasRef" class="matrix-rain" aria-hidden="true" />
</template>

<style lang="scss" scoped>
.matrix-rain {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  z-index: 0;
}
</style>
