<script setup lang="ts">
/**
 * views/user/Home.vue
 * 主页：业务功能入口 + 语音按钮
 * 笔记本：4-5 列；手机：2 列 + 底部固定语音按钮
 */
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { useRouter } from 'vue-router';
import RecognitionCard from '@/components/business/RecognitionCard.vue';
import VoiceButton from '@/components/business/VoiceButton.vue';
import { useResponsive } from '@/composables/useResponsive';
import { useTTS } from '@/composables/useTTS';
import { useVoiceWake } from '@/composables/useVoiceWake';
import { useSettingsStore } from '@/stores/settings';

const router = useRouter();
const { isMobile } = useResponsive();
const { speak } = useTTS();
const settings = useSettingsStore();

const features = [
  { title: '出行感知', description: '识别前方障碍、行人、红绿灯和台阶', icon: 'Promotion', routeName: 'Travel', shortcut: '1' },
  { title: '文档阅读', description: '拍照识别文字并语音朗读', icon: 'Reading', routeName: 'OCR', shortcut: '2' },
  { title: '货币识别', description: '识别人民币面额与真伪提示', icon: 'Money', routeName: 'Currency', shortcut: '3' },
  { title: '商品识别', description: '识别商品名称、品牌与规格', icon: 'Goods', routeName: 'Product', shortcut: '4' },
  { title: '人脸描述', description: '识别人物性别、年龄、表情与服饰', icon: 'User', routeName: 'Face', shortcut: '5' },
];

// 唤醒词：开启时启动
const wake = useVoiceWake({
  onCommand: (cmd) => {
    const text = cmd.toLowerCase();
    if (text.includes('出行')) router.push({ name: 'Travel' });
    else if (text.includes('文档') || text.includes('阅读') || text.includes('文字')) router.push({ name: 'OCR' });
    else if (text.includes('货币') || text.includes('钱')) router.push({ name: 'Currency' });
    else if (text.includes('商品')) router.push({ name: 'Product' });
    else if (text.includes('人脸') || text.includes('人')) router.push({ name: 'Face' });
    else if (text.includes('历史')) router.push({ name: 'History' });
    else if (text.includes('设置')) router.push({ name: 'Settings' });
  },
});

function handleKey(e: KeyboardEvent) {
  // 数字键 1-5 快捷跳转
  if (/^[1-5]$/.test(e.key)) {
    const idx = Number(e.key) - 1;
    if (features[idx]) router.push({ name: features[idx].routeName });
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKey);
  if (settings.wakeEnabled) {
    setTimeout(() => wake.start(), 500);
  }
  speak('欢迎使用 SightEcho 昭视智伴，点击或说出功能名称即可使用。');
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKey);
  wake.stop();
});
</script>

<template>
  <div class="home-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">功能中心</h1>
      <p class="page-desc">选择下方功能开始识别，或长按语音按钮说出您的需求</p>
    </header>

    <section class="feature-grid" aria-label="功能列表">
      <div
        v-for="(item, i) in features"
        :key="item.routeName"
        class="grid-item"
        :class="`grid-${i + 1}`"
      >
        <RecognitionCard
          :title="item.title"
          :description="item.description"
          :icon="item.icon"
          :route-name="item.routeName"
          :shortcut="item.shortcut"
        />
      </div>
    </section>

    <footer class="voice-area" :class="{ 'floating': isMobile }">
      <VoiceButton
        :size="isMobile ? 'large' : 'medium'"
        @send="(text) => {
          const lower = text.toLowerCase();
          if (lower.includes('出行')) router.push({ name: 'Travel' });
          else if (lower.includes('文档') || lower.includes('文字')) router.push({ name: 'OCR' });
          else if (lower.includes('货币') || lower.includes('钱')) router.push({ name: 'Currency' });
          else if (lower.includes('商品')) router.push({ name: 'Product' });
          else if (lower.includes('人脸')) router.push({ name: 'Face' });
          else speak(`收到：${text}`);
        }"
      />
    </footer>
  </div>
</template>

<style lang="scss" scoped>
.home-page {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding-bottom: 48px;
}
.home-page.mobile { padding-bottom: 200px; }
.page-header {
  text-align: center;
  margin-top: 8px;
}
.page-title {
  font-size: 28px;
  color: $text-main;
  margin: 0 0 8px;
}
.page-desc {
  color: $text-secondary;
  font-size: 15px;
  margin: 0;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.grid-5 { grid-column: span 1; }
@include laptop {
  .feature-grid { grid-template-columns: repeat(3, 1fr); }
  .grid-1, .grid-5 { grid-column: span 1; }
}
@include tablet {
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
}
@include mobile {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .page-title { font-size: 22px; }
}
.voice-area {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
}
.voice-area.floating {
  position: fixed;
  bottom: 24px;
  left: 0;
  right: 0;
  z-index: 30;
  padding: 16px;
  background: rgba(224, 229, 236, 0.9);
  backdrop-filter: blur(8px);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.06);
}
</style>
