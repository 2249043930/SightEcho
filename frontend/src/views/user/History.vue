<script setup lang="ts">
/**
 * views/user/History.vue
 * 历史记录：笔记本（列表+详情抽屉）/ 手机（列表+详情页）
 */
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getHistory, deleteHistory, type RecognitionResult, type RecognitionType } from '@/api/recognition';
import { useResponsive } from '@/composables/useResponsive';
import AudioPlayer from '@/components/business/AudioPlayer.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import { formatRelativeTime } from '@/utils/format';

const router = useRouter();
const { isMobile } = useResponsive();

const list = ref<RecognitionResult[]>([]);
const loading = ref(false);
const current = ref<RecognitionResult | null>(null);
const drawerOpen = ref(false);
const filterType = ref<RecognitionType | ''>('');
const keyword = ref('');

const typeLabels: Record<RecognitionType, string> = {
  travel: '出行',
  ocr: 'OCR',
  currency: '货币',
  product: '商品',
  face: '人脸',
};

const filtered = computed(() => {
  let r = list.value;
  if (filterType.value) r = r.filter((i) => i.type === filterType.value);
  if (keyword.value) {
    const k = keyword.value.toLowerCase();
    r = r.filter((i) => i.title.toLowerCase().includes(k) || i.content.toLowerCase().includes(k));
  }
  return r;
});

async function load() {
  loading.value = true;
  try {
    const resp = await getHistory({ page: 1, pageSize: 50, type: filterType.value || undefined });
    list.value = resp.list;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function open(item: RecognitionResult) {
  if (isMobile.value) {
    router.push({ name: 'HistoryDetail', query: { id: item.id } });
  } else {
    current.value = item;
    drawerOpen.value = true;
  }
}

async function handleDelete(item: RecognitionResult) {
  try {
    await deleteHistory(item.id);
    list.value = list.value.filter((i) => i.id !== item.id);
    if (current.value?.id === item.id) {
      current.value = null;
      drawerOpen.value = false;
    }
  } catch (e) {
    console.error(e);
  }
}

onMounted(load);
</script>

<template>
  <div class="history-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">历史记录</h1>
      <p class="page-desc">共 {{ list.length }} 条记录，点击查看详情或重听</p>
    </header>

    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索标题或内容"
        clearable
        size="default"
        style="max-width: 280px;"
        aria-label="搜索历史记录"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="filterType" placeholder="全部类型" clearable size="default" style="width: 140px;" aria-label="按类型筛选">
        <el-option label="出行" value="travel" />
        <el-option label="OCR" value="ocr" />
        <el-option label="货币" value="currency" />
        <el-option label="商品" value="product" />
        <el-option label="人脸" value="face" />
      </el-select>
    </div>

    <div v-if="loading" class="loading" aria-busy="true">加载中…</div>
    <EmptyState
      v-else-if="!filtered.length"
      title="还没有记录"
      description="完成一次识别后，记录会自动出现在这里"
      icon="Clock"
    />
    <ul v-else class="history-list" role="list">
      <li
        v-for="item in filtered"
        :key="item.id"
        class="history-item"
        role="listitem"
      >
        <button class="item-btn" @click="open(item)" :aria-label="`${typeLabels[item.type]}识别：${item.title}，${formatRelativeTime(item.createdAt)}`">
          <div class="item-icon" aria-hidden="true">
            <el-icon :size="24">
              <component :is="item.type === 'travel' ? 'Promotion' : item.type === 'ocr' ? 'Reading' : item.type === 'currency' ? 'Money' : item.type === 'product' ? 'Goods' : 'User'" />
            </el-icon>
          </div>
          <div class="item-content">
            <h3 class="item-title">{{ item.title }}</h3>
            <p class="item-desc">{{ item.content }}</p>
            <div class="item-meta">
              <span class="type-tag" :class="`type-${item.type}`">{{ typeLabels[item.type] }}</span>
              <span class="time">{{ formatRelativeTime(item.createdAt) }}</span>
            </div>
          </div>
        </button>
        <button class="item-delete" :aria-label="`删除 ${item.title}`" @click="handleDelete(item)">
          <el-icon :size="18"><Delete /></el-icon>
        </button>
      </li>
    </ul>

    <!-- 笔记本端：右侧抽屉 -->
    <el-drawer
      v-if="!isMobile"
      v-model="drawerOpen"
      direction="rtl"
      size="480px"
      :with-header="false"
    >
      <div v-if="current" class="detail-pane">
        <header class="detail-header">
          <h2 class="detail-title">{{ current.title }}</h2>
          <span class="detail-time">{{ formatRelativeTime(current.createdAt) }}</span>
        </header>
        <p class="detail-content">{{ current.content }}</p>
        <AudioPlayer :audio-url="current.audioUrl" :text="current.content" :auto-play="false" />
      </div>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>
.history-page { display: flex; flex-direction: column; gap: 16px; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.loading { text-align: center; padding: 24px; color: $text-secondary; }
.history-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
@include laptop {
  .history-list { grid-template-columns: repeat(2, 1fr); }
}
.history-item {
  position: relative;
  display: flex;
  background: $bg-main;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  transition: $transition-base;
  &:hover { box-shadow: $shadow-md; }
}
.item-btn {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
  color: $text-main;
  border-radius: $radius-md;
  &:focus-visible {
    outline: 2px solid $accent;
    outline-offset: -2px;
  }
}
.item-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-elevated;
  border-radius: $radius-md;
  color: $accent;
  flex-shrink: 0;
  box-shadow: inset 2px 2px 4px $shadow-dark, inset -2px -2px 4px $shadow-light;
}
.item-content { flex: 1; min-width: 0; }
.item-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-main;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-desc {
  font-size: 14px;
  color: $text-secondary;
  margin: 0 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.item-meta { display: flex; gap: 8px; align-items: center; font-size: 12px; color: $text-muted; }
.type-tag {
  padding: 2px 8px;
  border-radius: $radius-sm;
  font-weight: 500;
  background: $bg-elevated;
  color: $accent;
  &.type-travel { color: #409EFF; }
  &.type-ocr { color: #67C23A; }
  &.type-currency { color: $color-warning; }
  &.type-product { color: $color-success; }
  &.type-face { color: $accent; }
}
.item-delete {
  align-self: flex-start;
  width: 40px;
  height: 40px;
  margin: 8px 12px 0 0;
  background: transparent;
  border: 0;
  border-radius: 50%;
  color: $text-muted;
  cursor: pointer;
  transition: $transition-fast;
  &:hover { background: rgba(227, 107, 107, 0.1); color: $color-danger; }
  &:focus-visible { outline: 2px solid $accent; }
}
.detail-pane { padding: 24px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-title { font-size: 20px; color: $text-main; margin: 0; }
.detail-time { color: $text-muted; font-size: 13px; }
.detail-content { color: $text-main; line-height: 1.7; font-size: 16px; margin: 0 0 16px; }
:deep(.el-drawer) { background: $bg-main !important; }
</style>
