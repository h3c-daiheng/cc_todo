<template>
  <div class="page">
    <div class="header">
      <h2>甘特图</h2>
    </div>

    <div class="toolbar">
      <el-radio-group v-model="viewMode" @change="load">
        <el-radio-button value="personal">我的任务</el-radio-button>
        <el-radio-button value="team">团队视图</el-radio-button>
      </el-radio-group>

      <el-select
        v-if="viewMode === 'team'"
        v-model="selectedTeamId"
        placeholder="选择团队"
        style="width:160px"
        @change="load"
      >
        <el-option v-for="t in teams" :key="t.id" :value="t.id" :label="t.name" />
      </el-select>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始"
        end-placeholder="结束"
        value-format="YYYY-MM-DD"
        :shortcuts="dateShortcuts"
        style="width:260px"
        @change="load"
      />
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" />

    <el-card v-if="ganttTasks.length > 0">
      <v-chart :option="ganttOption" :style="`height:${Math.max(ganttTasks.length * 40 + 60, 200)}px`" autoresize />
    </el-card>
    <el-empty v-else-if="!loading" description="暂无可显示的任务（需要设置截止日期）" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api/index.js'
import { fetchAllTasks } from '../api/tasks.js'

use([CanvasRenderer, CustomChart, TooltipComponent, GridComponent, DataZoomComponent])

const viewMode = ref('personal')
const selectedTeamId = ref(null)
const teams = ref([])
const allTasks = ref([])
const error = ref(null)
const loading = ref(false)
const today = new Date().toISOString().slice(0, 10)

const monthStart = today.slice(0, 8) + '01'
const monthEnd = new Date(today.slice(0, 4), Number(today.slice(5, 7)), 0).toISOString().slice(0, 10)
const dateRange = ref([monthStart, monthEnd])

const dateShortcuts = [
  {
    text: '本周',
    value: () => {
      const now = new Date()
      const day = now.getDay() || 7
      const start = new Date(now); start.setDate(now.getDate() - day + 1)
      const end = new Date(start); end.setDate(start.getDate() + 6)
      return [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)]
    }
  },
  { text: '本月', value: () => [monthStart, monthEnd] }
]

const ganttTasks = computed(() => {
  const [rangeStart, rangeEnd] = dateRange.value || [null, null]
  return allTasks.value.filter(t => {
    if (!t.due_date) return false
    if (rangeEnd && t.due_date > rangeEnd) return false
    const taskStart = t.start_date || t.due_date
    if (rangeStart && taskStart < rangeStart) return false
    return true
  })
})

const statusColors = { pending: '#e6a23c', in_progress: '#409eff', done: '#67c23a', overdue: '#f56c6c' }

function taskStatus(t) {
  if (t.status === 'done') return 'done'
  if (t.due_date && t.due_date < today) return 'overdue'
  return t.status
}

const ganttOption = computed(() => {
  const tasks = ganttTasks.value
  const [rangeStart, rangeEnd] = dateRange.value || [monthStart, monthEnd]

  return {
    tooltip: {
      formatter: (params) => {
        const t = tasks[params.dataIndex]
        return `<b>${t.title}</b><br/>状态: ${t.status}<br/>开始: ${t.start_date || '—'}<br/>截止: ${t.due_date}`
      }
    },
    grid: { top: 10, right: 20, bottom: 60, left: 160, containLabel: false },
    xAxis: {
      type: 'time',
      min: rangeStart,
      max: rangeEnd,
      axisLabel: {
        formatter: (val) => new Date(val).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
      },
    },
    yAxis: {
      type: 'category',
      data: tasks.map(t => t.title.length > 12 ? t.title.slice(0, 12) + '…' : t.title),
      axisLabel: { fontSize: 12 },
    },
    dataZoom: [{ type: 'slider', bottom: 10 }],
    series: [{
      type: 'custom',
      renderItem(params, api) {
        const t = tasks[params.dataIndex]
        const start = t.start_date || t.due_date
        const end = t.due_date
        const x1 = api.coord([start, params.dataIndex])[0]
        const x2 = api.coord([end, params.dataIndex])[0]
        const y = api.coord([start, params.dataIndex])[1]
        const barHeight = 18
        const color = statusColors[taskStatus(t)]
        const width = Math.max(x2 - x1, 4)
        return {
          type: 'rect',
          shape: { x: x1, y: y - barHeight / 2, width, height: barHeight },
          style: { fill: color, borderRadius: 3 },
        }
      },
      data: tasks.map((_, i) => i),
      encode: { x: [0, 1], y: 2 },
    }],
  }
})

async function load() {
  loading.value = true
  error.value = null
  try {
    if (viewMode.value === 'team' && !selectedTeamId.value) {
      allTasks.value = []
      return
    }
    const params = viewMode.value === 'team' ? { team_id: selectedTeamId.value } : {}
    allTasks.value = await fetchAllTasks(params)
  } catch {
    error.value = '加载任务失败'
    allTasks.value = []
  } finally {
    loading.value = false
  }
}

async function loadTeams() {
  try {
    const res = await api.get('/teams')
    teams.value = res.data || res || []
  } catch { teams.value = [] }
}

onMounted(async () => {
  await loadTeams()
  await load()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
