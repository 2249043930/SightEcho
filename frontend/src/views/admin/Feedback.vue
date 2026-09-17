<script setup lang="ts">
/**
 * views/admin/Feedback.vue
 * 用户反馈列表
 */
import { ref, onMounted } from 'vue';
import { listFeedback, resolveFeedback, type FeedbackItem } from '@/api/admin';
import { formatDateTime } from '@/utils/format';
import { ElMessage } from 'element-plus';

const list = ref<FeedbackItem[]>([]);
const loading = ref(false);
const filterStatus = ref<'pending' | 'resolved' | ''>('');

async function load() {
  loading.value = true;
  try {
    const resp = await listFeedback({
      status: filterStatus.value || undefined,
      page: 1,
      pageSize: 100,
    });
    list.value = resp.list;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleResolve(item: FeedbackItem) {
  try {
    await resolveFeedback(item.id);
    ElMessage.success('已标记为已处理');
    await load();
  } catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <div class="feedback-page">
    <header class="page-header">
      <h1 class="page-title">用户反馈</h1>
      <p class="page-desc">查看并处理用户提交的反馈</p>
    </header>

    <div class="toolbar">
      <el-radio-group v-model="filterStatus" @change="load">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">未处理</el-radio-button>
        <el-radio-button value="resolved">已处理</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="loading" class="loading" aria-busy="true">加载中…</div>
    <ul v-else class="feedback-list" role="list">
      <li v-for="item in list" :key="item.id" class="feedback-item" role="listitem">
        <div class="item-head">
          <div class="meta">
            <span class="rating" :aria-label="`评分：${item.rating} 星`">
              <el-icon v-for="i in 5" :key="i" :size="16">
                <component :is="i <= item.rating ? 'StarFilled' : 'Star'" />
              </el-icon>
            </span>
            <span class="time">{{ formatDateTime(item.createdAt) }}</span>
          </div>
          <el-tag :type="item.status === 'resolved' ? 'success' : 'warning'">
            {{ item.status === 'resolved' ? '已处理' : '未处理' }}
          </el-tag>
        </div>
        <p v-if="item.comment" class="comment">{{ item.comment }}</p>
        <div class="actions">
          <button v-if="item.status !== 'resolved'" class="row-btn primary" @click="handleResolve(item)">
            标记为已处理
          </button>
        </div>
      </li>
      <p v-if="!list.length" class="empty">暂无反馈</p>
    </ul>
  </div>
</template>

<style lang="scss" scoped>
.feedback-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.toolbar { display: flex; justify-content: flex-end; }
.loading { text-align: center; padding: 24px; color: $text-secondary; }
.feedback-list { display: flex; flex-direction: column; gap: 12px; }
.feedback-item {
  background: $bg-main;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.item-head { display: flex; justify-content: space-between; align-items: center; }
.meta { display: flex; gap: 12px; align-items: center; color: $text-muted; font-size: 13px; }
.rating { color: $color-warning; display: inline-flex; gap: 2px; }
.comment { color: $text-main; font-size: 15px; line-height: 1.6; margin: 0; }
.actions { display: flex; justify-content: flex-end; }
.row-btn {
  height: 36px;
  padding: 0 16px;
  background: $bg-main;
  border: 0;
  border-radius: $radius-sm;
  box-shadow: $shadow-sm;
  color: $text-main;
  cursor: pointer;
  font-size: 13px;
  &.primary { background: $accent; color: #fff; }
  &:hover { box-shadow: $shadow-md; }
  &:focus-visible { outline: 2px solid $accent; outline-offset: 2px; }
}
.empty { text-align: center; color: $text-muted; padding: 32px; }
:deep(.el-radio-button__inner) { background: $bg-main !important; color: $text-main !important; border-color: $shadow-dark !important; box-shadow: $shadow-sm !important; }
:deep(.el-radio-button.is-active .el-radio-button__inner) { background: $accent !important; color: #fff !important; box-shadow: $shadow-inset-sm !important; }
</style>
