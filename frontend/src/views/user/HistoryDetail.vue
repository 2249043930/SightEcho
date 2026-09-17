<script setup lang="ts">
/**
 * views/user/HistoryDetail.vue
 * 历史记录详情页（手机端使用）
 */
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getHistoryDetail, type RecognitionResult } from '@/api/recognition';
import { deleteHistory } from '@/api/recognition';
import AudioPlayer from '@/components/business/AudioPlayer.vue';
import { formatDateTime } from '@/utils/format';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const item = ref<RecognitionResult | null>(null);
const loading = ref(false);

async function load() {
  const id = route.query.id as string;
  if (!id) return;
  loading.value = true;
  try {
    item.value = await getHistoryDetail(id);
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleDelete() {
  if (!item.value) return;
  await deleteHistory(item.value.id);
  ElMessage.success('已删除');
  router.replace({ name: 'History' });
}

onMounted(load);
watch(() => route.query.id, load);
</script>

<template>
  <div class="detail-page">
    <header class="page-header">
      <button class="back-btn" aria-label="返回历史记录" @click="router.back()">
        <el-icon :size="24"><ArrowLeft /></el-icon>
      </button>
      <h1 class="page-title">{{ item?.title || '详情' }}</h1>
    </header>

    <div v-if="loading" class="loading" aria-busy="true">加载中…</div>
    <article v-else-if="item" class="detail-content">
      <div class="meta">
        <span class="time">{{ formatDateTime(item.createdAt) }}</span>
        <span class="type">{{ item.type }}</span>
      </div>
      <p class="content">{{ item.content }}</p>
      <div class="actions">
        <AudioPlayer :audio-url="item.audioUrl" :text="item.content" />
        <button class="delete-btn" @click="handleDelete">
          <el-icon :size="18"><Delete /></el-icon>
          <span>删除</span>
        </button>
      </div>
    </article>
  </div>
</template>

<style lang="scss" scoped>
.detail-page { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; gap: 12px; }
.back-btn {
  width: 48px;
  height: 48px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; }
}
.page-title { font-size: 22px; color: $text-main; margin: 0; }
.loading { text-align: center; padding: 48px; color: $text-secondary; }
.detail-content {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.meta { display: flex; justify-content: space-between; color: $text-muted; font-size: 13px; }
.content { color: $text-main; font-size: 18px; line-height: 1.7; margin: 0; white-space: pre-wrap; }
.actions { display: flex; justify-content: space-between; align-items: center; padding-top: 8px; border-top: 1px solid rgba(184, 188, 194, 0.3); }
.delete-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 40px;
  padding: 0 14px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  color: $color-danger;
  cursor: pointer;
  font-size: 14px;
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; }
}
</style>
