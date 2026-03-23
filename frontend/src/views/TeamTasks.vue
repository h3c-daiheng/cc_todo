<template>
  <div class="page">
    <div class="header">
      <h2>{{ team ? team.name : '团队任务' }}</h2>
      <div class="header-actions">
        <el-button @click="goManage">管理成员</el-button>
        <el-button type="primary" @click="showCreate = true">+ 新建任务</el-button>
      </div>
    </div>

    <task-board :tasks="tasks" @update-status="updateStatus" @task-click="goDetail" />

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
        <el-form-item label="负责人">
          <el-select v-model="newTask.assigned_to" placeholder="选择成员" clearable>
            <el-option
              v-for="m in members"
              :key="m.user_id"
              :value="m.user_id"
              :label="m.username"
            />
          </el-select>
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
import { ref, onMounted, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'
import TaskBoard from '../components/TaskBoard.vue'

const route = useRoute()
const router = useRouter()
const teamId = computed(() => Number(route.params.id))

const team = ref(null)
const members = ref([])
const tasks = ref([])
const showCreate = ref(false)
const newTask = reactive({ title: '', priority: 'medium', due_date: null, start_date: null, assigned_to: null, labelsInput: '' })

async function loadTeam() {
  try {
    const res = await api.get(`/teams/${teamId.value}`)
    const data = res.data || res
    team.value = data
    members.value = data.members || []
  } catch (e) {
    ElMessage.error('加载团队信息失败')
  }
}

async function loadTasks() {
  try {
    const res = await api.get('/tasks')
    const items = res.items || (res.data && res.data.items) || []
    tasks.value = items.filter(t => t.team_id === teamId.value)
  } catch (e) {
    ElMessage.error('加载任务失败')
  }
}

async function createTask() {
  const payload = {
    title: newTask.title,
    priority: newTask.priority,
    due_date: newTask.due_date || null,
    start_date: newTask.start_date || null,
    assigned_to: newTask.assigned_to || null,
    team_id: teamId.value,
    labels: newTask.labelsInput ? newTask.labelsInput.split(',').map(s => s.trim()).filter(Boolean) : []
  }
  try {
    await api.post('/tasks', payload)
    showCreate.value = false
    Object.assign(newTask, { title: '', priority: 'medium', due_date: null, start_date: null, assigned_to: null, labelsInput: '' })
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

function goDetail(task) { router.push(`/task/${task.id}`) }
function goManage() { router.push(`/team/${teamId.value}/manage`) }

onMounted(async () => {
  await loadTeam()
  await loadTasks()
})
</script>

<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
.header-actions { display: flex; gap: 8px; }
</style>
