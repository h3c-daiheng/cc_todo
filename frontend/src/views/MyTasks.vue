<template>
  <div class="page">
    <div class="header">
      <div>
        <h2>我的任务</h2>
        <div class="task-count">共 {{ filteredTasks.length }} 个任务</div>
      </div>
      <el-button type="primary" @click="showCreate = true" class="btn-new">+ 新建任务</el-button>
    </div>

    <div class="filters">
      <el-select v-model="filter.priority" placeholder="优先级" clearable @change="loadTasks" style="width:120px">
        <el-option value="high" label="高" />
        <el-option value="medium" label="中" />
        <el-option value="low" label="低" />
      </el-select>
      <el-select v-model="filter.status" placeholder="状态" clearable @change="loadTasks" style="width:120px">
        <el-option value="pending" label="待处理" />
        <el-option value="in_progress" label="进行中" />
        <el-option value="done" label="已完成" />
      </el-select>
    </div>

    <div class="toolbar">
      <el-input v-model="searchQuery" placeholder="搜索任务..." clearable style="width:200px" />
      <el-radio-group v-model="currentView">
        <el-radio-button label="board">看板</el-radio-button>
        <el-radio-button label="list">列表</el-radio-button>
        <el-radio-button label="calendar">日历</el-radio-button>
      </el-radio-group>
    </div>

    <quick-task-input @task-create="handleQuickCreate" />

    <task-board v-if="currentView === 'board'" :tasks="filteredTasks" @update-status="updateStatus" @task-click="goDetail" />
    <task-list v-else-if="currentView === 'list'" :tasks="filteredTasks" @status-change="handleListStatusChange" @view-detail="goDetail" />
    <task-calendar v-else :tasks="filteredTasks" />

    <el-dialog v-model="showCreate" title="新建任务" width="500px">
      <el-form :model="newTask" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="newTask.title" placeholder="任务标题" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="newTask.priority">
            <el-option value="high" label="高" />
            <el-option value="medium" label="中" />
            <el-option value="low" label="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="newTask.due_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="newTask.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="newTask.labelsInput" placeholder="逗号分隔，如：bug,紧急" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createTask" :disabled="!newTask.title">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'
import TaskBoard from '../components/TaskBoard.vue'
import TaskList from '../components/TaskList.vue'
import TaskCalendar from '../components/TaskCalendar.vue'
import QuickTaskInput from '../components/QuickTaskInput.vue'

const router = useRouter()
const tasks = ref([])
const showCreate = ref(false)
const filter = reactive({ priority: '', status: '' })
const searchQuery = ref('')
const currentView = ref(localStorage.getItem('myTasksView') || 'board')
const newTask = reactive({ title: '', priority: 'medium', due_date: null, start_date: null, labelsInput: '' })

watch(currentView, (newVal) => {
  localStorage.setItem('myTasksView', newVal)
})

const filteredTasks = computed(() => {
  let result = tasks.value

  if (filter.priority) {
    result = result.filter(t => t.priority === filter.priority)
  }

  if (filter.status) {
    result = result.filter(t => t.status === filter.status)
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      (t.title && t.title.toLowerCase().includes(q)) ||
      (t.description && t.description.toLowerCase().includes(q))
    )
  }

  return result
})

async function loadTasks() {
  const params = {}
  if (filter.priority) params.priority = filter.priority
  if (filter.status) params.status = filter.status
  try {
    const res = await api.get('/tasks', { params })
    const items = res.items || (res.data && res.data.items) || []
    tasks.value = items
  } catch (e) {
    ElMessage.error('加载任务失败')
  }
}

async function handleQuickCreate(title) {
  try {
    await api.post('/tasks', { title, priority: 'medium' })
    await loadTasks()
    ElMessage.success('任务已创建')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

async function createTask() {
  const payload = {
    title: newTask.title,
    priority: newTask.priority,
    due_date: newTask.due_date || null,
    start_date: newTask.start_date || null,
    labels: newTask.labelsInput ? newTask.labelsInput.split(',').map(s => s.trim()).filter(Boolean) : []
  }
  try {
    await api.post('/tasks', payload)
    showCreate.value = false
    Object.assign(newTask, { title: '', priority: 'medium', due_date: null, start_date: null, labelsInput: '' })
    await loadTasks()
    ElMessage.success('任务已创建')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

async function updateStatus({ taskId, status }) {
  try {
    await api.patch(`/tasks/${taskId}/status`, { status })
    await loadTasks()
  } catch (e) {
    ElMessage.error('更新状态失败')
  }
}

function handleListStatusChange(taskId, status) {
  updateStatus({ taskId, status })
}

function goDetail(taskId) {
  router.push(`/task/${taskId}`)
}

onMounted(loadTasks)
</script>

<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.task-count { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.btn-new { border-radius: 10px; font-weight: 600; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.toolbar { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
</style>
