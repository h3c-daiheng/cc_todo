<template>
  <div class="page" v-if="task">
    <el-page-header @back="router.back()">
      <template #content>{{ task.title }}</template>
      <template #extra>
        <el-button type="danger" @click="deleteTask">删除</el-button>
      </template>
    </el-page-header>

    <el-card class="detail-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">
          <el-select v-model="task.status" @change="updateStatus" style="width:130px">
            <el-option value="pending" label="待处理" />
            <el-option value="in_progress" label="进行中" />
            <el-option value="done" label="已完成" />
          </el-select>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="priorityType">{{ priorityLabel }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="截止日期">
          <span :class="{ urgent: isUrgent }">{{ task.due_date || '—' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="负责人">用户 #{{ task.assigned_to || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <template v-if="task.labels?.length">
            <el-tag v-for="l in task.labels" :key="l" size="small" style="margin:2px">{{ l }}</el-tag>
          </template>
          <span v-else style="color:#aaa">—</span>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ task.description || '—' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="section-card">
      <template #header><span class="section-title">附件</span></template>
      <file-upload :task-id="task.id" :attachments="task.attachments || []" @refresh="loadTask" />
    </el-card>

    <el-card class="section-card">
      <template #header><span class="section-title">评论</span></template>
      <comment-list :task-id="task.id" :comments="task.comments || []" @refresh="loadTask" />
    </el-card>
  </div>

  <div v-else-if="loading" class="page loading">
    <el-skeleton :rows="5" animated />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import CommentList from '../components/CommentList.vue'
import FileUpload from '../components/FileUpload.vue'

const route = useRoute()
const router = useRouter()
const task = ref(null)
const loading = ref(true)

const priorityMap = { high: ['danger', '高'], medium: ['warning', '中'], low: ['info', '低'] }
const priorityType = computed(() => priorityMap[task.value?.priority]?.[0] || 'info')
const priorityLabel = computed(() => priorityMap[task.value?.priority]?.[1] || '')
const isUrgent = computed(() => {
  if (!task.value?.due_date) return false
  return (new Date(task.value.due_date) - new Date()) / 86400000 <= 1
})

async function loadTask() {
  try {
    const res = await api.get(`/tasks/${route.params.id}`)
    task.value = res.data || res
  } catch (e) {
    ElMessage.error('加载任务失败')
    router.back()
  } finally {
    loading.value = false
  }
}

async function updateStatus(status) {
  try {
    await api.patch(`/tasks/${task.value.id}/status`, { status })
    ElMessage.success('状态已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    await loadTask() // revert
  }
}

async function deleteTask() {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.delete(`/tasks/${task.value.id}`)
    ElMessage.success('任务已删除')
    router.back()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(loadTask)
</script>

<style scoped>
.page { padding: 24px; max-width: 900px; }
.detail-card { margin-top: 20px; border-radius: 12px; border: 1px solid var(--border); }
.section-card { margin-top: 16px; border-radius: 12px; border: 1px solid var(--border); }
.section-title { font-weight: 600; color: var(--text-primary); }
.urgent { color: var(--danger); font-weight: 600; }
.loading { padding-top: 60px; }
</style>
