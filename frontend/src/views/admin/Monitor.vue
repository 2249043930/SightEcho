<script setup lang="ts">
/**
 * views/admin/Monitor.vue
 * 接口监控：实时 QPS / 成功率 / 平均耗时（每 5s 轮询）
 */
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { getMonitor, type MonitorResp } from '@/api/admin';
import { formatPercent } from '@/utils/format';

const data = ref<MonitorResp | null>(null);
const loading = ref(false);
let timer: number | null = null;

async function load() {
  try {
    data.value = await getMonitor();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  load();
  timer = window.setInterval(load, 5000);
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="monitor-page">
    <header class="page-header">
      <h1 class="page-title">接口监控</h1>
      <p class="page-desc">每 5 秒自动刷新实时数据</p>
    </header>

    <section class="metric-grid">
      <article class="metric-card">
        <div class="metric-label">QPS</div>
        <div class="metric-value">{{ data?.qps?.toFixed(2) ?? '--' }}</div>
      </article>
      <article class="metric-card">
        <div class="metric-label">成功率</div>
        <div class="metric-value">
          {{ data ? `${data.successRate.toFixed(2)}%` : '--' }}
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-label">平均耗时</div>
        <div class="metric-value">{{ data ? `${data.avgLatency.toFixed(0)} ms` : '--' }}</div>
      </article>
    </section>

    <section class="endpoint-card">
      <h2 class="section-title">接口详情</h2>
      <el-table :data="data?.endpoints || []" stripe>
        <el-table-column prop="path" label="路径" />
        <el-table-column label="QPS" width="120">
          <template #default="{ row }">{{ row.qps.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="成功" width="100">
          <template #default="{ row }">{{ row.success }}</template>
        </el-table-column>
        <el-table-column label="失败" width="100">
          <template #default="{ row }">{{ row.fail }}</template>
        </el-table-column>
        <el-table-column label="成功率" width="120">
          <template #default="{ row }">
            {{ formatPercent(row.success, row.success + row.fail) }}
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style lang="scss" scoped>
.monitor-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@include mobile { .metric-grid { grid-template-columns: 1fr; } }
.metric-card {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 24px;
  text-align: center;
}
.metric-label { color: $text-secondary; font-size: 14px; margin-bottom: 8px; }
.metric-value { color: $accent; font-size: 32px; font-weight: 700; }
.endpoint-card {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 20px;
}
.section-title { font-size: 18px; color: $text-main; margin: 0 0 16px; font-weight: 600; }
</style>
