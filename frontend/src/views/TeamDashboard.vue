<template>
  <div class="page">
    <div class="header">
      <h2>{{ teamName }} — 团队仪表盘</h2>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" />

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">待处理</div>
        <div class="stat-value pending">{{ stats.statusCounts.value.pending }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">进行中</div>
        <div class="stat-value in-progress">{{ stats.statusCounts.value.in_progress }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已完成</div>
        <div class="stat-value done">{{ stats.statusCounts.value.done }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已逾期</div>
        <div class="stat-value overdue">{{ stats.overdueCount.value }}</div>
      </div>
    </div>

    <div class="chart-row">
      <el-card class="chart-card">
        <template #header>优先级分布</template>
        <v-chart :option="priorityChartOption" style="height:200px" autoresize />
      </el-card>
      <el-card class="chart-card">
        <template #header>近 14 天完成趋势</template>
        <v-chart :option="trendChartOption" style="height:200px" autoresize />
      </el-card>
    </div>

    <el-card v-if="stats.overdueCount.value > 0" style="margin-top:16px">
      <template #header>
        <span style="color:#f56c6c">逾期任务 ({{ stats.overdueCount.value }})</span>
      </template>
      <el-table :data="stats.overdueTasks.value" size="small">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="due_date" label="截止日期" width="120" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="{ high: 'danger', medium: 'warning', low: 'info' }[row.priority]" size="small">
              {{ { high: '高', medium: '中', low: '低' }[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="members.length > 0" style="margin-top:16px">
      <template #header>成员工作量（未完成任务数）</template>
      <v-chart :option="workloadChartOption" :style="`height:${Math.max(members.length * 36 + 40, 120)}px`" autoresize />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api/index.js'
import { fetchAllTasks } from '../api/tasks.js'
import { useTaskStats } from '../composables/useTaskStats.js'

use([CanvasRenderer, PieChart, LineChart, BarChart, TooltipComponent, LegendComponent, GridComponent])

const route = useRoute()
const router = useRouter()
const teamName = ref('团队')
const members = ref([])
const tasks = ref([])
const error = ref(null)
const stats = useTaskStats(tasks)

const priorityChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: stats.priorityCounts.value.high, name: '高', itemStyle: { color: '#f56c6c' } },
      { value: stats.priorityCounts.value.medium, name: '中', itemStyle: { color: '#e6a23c' } },
      { value: stats.priorityCounts.value.low, name: '低', itemStyle: { color: '#909399' } },
    ],
  }],
}))

const trendChartOption = computed(() => {
  const trend = stats.completionTrend(14)
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 10, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: trend.map(d => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', data: trend.map(d => d.count), smooth: true, areaStyle: {} }],
  }
})

const workloadChartOption = computed(() => {
  const workload = stats.memberWorkload(members.value)
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 30, bottom: 10, left: 80, containLabel: true },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: members.value.map(m => m.username) },
    series: [{
      type: 'bar',
      data: members.value.map(m => workload[m.user_id] || 0),
      itemStyle: { color: '#409eff' },
    }],
  }
})

async function load() {
  try {
    const teamRes = await api.get(`/teams/${route.params.id}`)
    teamName.value = teamRes.data?.name || '团队'
    members.value = teamRes.data?.members || []
    tasks.value = await fetchAllTasks({ team_id: route.params.id })
  } catch (e) {
    if (e.response?.status === 403) {
      router.push('/dashboard')
    } else {
      error.value = '加载团队数据失败'
    }
  }
}

onMounted(load)
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.stat-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-value.pending { color: #e6a23c; }
.stat-value.in-progress { color: #409eff; }
.stat-value.done { color: #67c23a; }
.stat-value.overdue { color: #f56c6c; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chart-card { min-height: 260px; }
</style>
