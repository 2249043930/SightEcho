<script setup lang="ts">
/**
 * views/admin/Dashboard.vue
 * 管理员控制台：4 个统计卡片 + 2 个图表
 */
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { getAdminStats, type AdminStatsResp } from '@/api/admin';
import { useResponsive } from '@/composables/useResponsive';

const { isMobile } = useResponsive();
const stats = ref<AdminStatsResp | null>(null);
const loading = ref(false);

let chartLine: any = null;
let chartPie: any = null;
const lineRef = ref<HTMLDivElement | null>(null);
const pieRef = ref<HTMLDivElement | null>(null);

async function load() {
  loading.value = true;
  try {
    stats.value = await getAdminStats();
    await nextTick();
    renderCharts();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function nextTick() {
  return new Promise<void>((r) => requestAnimationFrame(() => r()));
}

async function renderCharts() {
  if (!stats.value) return;
  const echarts = await import('echarts');
  if (lineRef.value) {
    chartLine = echarts.init(lineRef.value);
    chartLine.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 30 },
      xAxis: {
        type: 'category',
        data: stats.value.trend.map((t) => t.date),
        axisLine: { lineStyle: { color: '#8a93a0' } },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#8a93a0' } },
        splitLine: { lineStyle: { color: '#b8bcc2' } },
      },
      series: [
        {
          data: stats.value.trend.map((t) => t.calls),
          type: 'line',
          smooth: true,
          lineStyle: { color: '#6d5dfc', width: 3 },
          itemStyle: { color: '#6d5dfc' },
          areaStyle: { color: 'rgba(109, 93, 252, 0.15)' },
        },
      ],
    });
  }
  if (pieRef.value) {
    chartPie = echarts.init(pieRef.value);
    chartPie.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: stats.value.distribution,
          label: { color: '#2c2c34' },
        },
      ],
    });
  }
}

function resizeCharts() {
  chartLine?.resize();
  chartPie?.resize();
}

onMounted(() => {
  load();
  window.addEventListener('resize', resizeCharts);
});
onBeforeUnmount(() => {
  chartLine?.dispose();
  chartPie?.dispose();
  window.removeEventListener('resize', resizeCharts);
});
</script>

<template>
  <div class="dashboard-page" :class="{ mobile: isMobile }">
    <header class="page-header">
      <h1 class="page-title">管理控制台</h1>
      <p class="page-desc">SightEcho 系统总览</p>
    </header>

    <section class="stat-grid" aria-label="统计数据">
      <article class="stat-card">
        <div class="stat-icon" aria-hidden="true">👥</div>
        <div class="stat-value">{{ stats?.totalUsers ?? '--' }}</div>
        <div class="stat-label">总用户数</div>
      </article>
      <article class="stat-card">
        <div class="stat-icon" aria-hidden="true">📈</div>
        <div class="stat-value">{{ stats?.todayActive ?? '--' }}</div>
        <div class="stat-label">今日活跃</div>
      </article>
      <article class="stat-card">
        <div class="stat-icon" aria-hidden="true">🔍</div>
        <div class="stat-value">{{ stats?.todayCalls ?? '--' }}</div>
        <div class="stat-label">今日调用</div>
      </article>
      <article class="stat-card">
        <div class="stat-icon" aria-hidden="true">✅</div>
        <div class="stat-value">{{ stats ? `${stats.successRate.toFixed(1)}%` : '--' }}</div>
        <div class="stat-label">成功率</div>
      </article>
    </section>

    <section class="chart-row" :class="{ mobile: isMobile }">
      <article class="chart-card">
        <h2 class="chart-title">近 7 日调用量</h2>
        <div ref="lineRef" class="chart" style="height: 320px;" />
      </article>
      <article class="chart-card">
        <h2 class="chart-title">业务类型分布</h2>
        <div ref="pieRef" class="chart" style="height: 320px;" />
      </article>
    </section>
  </div>
</template>

<style lang="scss" scoped>
.dashboard-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { text-align: center; }
.page-title { font-size: 24px; color: $text-main; margin: 0 0 4px; }
.page-desc { color: $text-secondary; font-size: 14px; margin: 0; }
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
@include mobile { .stat-grid { grid-template-columns: 1fr; } }
@include tablet { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 24px 16px;
  gap: 8px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  background: $bg-main;
  border-radius: 50%;
  box-shadow: inset 4px 4px 8px $shadow-dark, inset -4px -4px 8px $shadow-light;
  margin-bottom: 4px;
}
.stat-value { font-size: 28px; font-weight: 700; color: $text-main; }
.stat-label { color: $text-secondary; font-size: 14px; }
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.chart-row.mobile { grid-template-columns: 1fr; }
.chart-card {
  background: $bg-main;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: 20px;
}
.chart-title { font-size: 16px; color: $text-main; margin: 0 0 12px; font-weight: 600; }
.chart { width: 100%; }
</style>
