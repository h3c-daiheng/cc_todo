<template>
  <div>
    <el-upload
      :action="`/api/v1/tasks/${taskId}/attachments`"
      :headers="uploadHeaders"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="onSuccess"
      :on-error="onError"
    >
      <el-button size="small" type="default">
        <el-icon><Upload /></el-icon> 上传附件
      </el-button>
    </el-upload>

    <div v-if="attachments.length" class="att-list">
      <div v-for="att in attachments" :key="att.id" class="att-item">
        <el-icon><Paperclip /></el-icon>
        <a :href="`/api/v1/attachments/${att.id}/download`" target="_blank" class="att-name">
          {{ att.filename }}
        </a>
        <span class="att-size">{{ formatSize(att.file_size) }}</span>
      </div>
    </div>
    <div v-else class="empty">暂无附件</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '../api/index.js'

const props = defineProps({
  taskId: Number,
  attachments: { type: Array, default: () => [] }
})
const emit = defineEmits(['refresh'])

const uploadHeaders = computed(() => {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
})

function beforeUpload(file) {
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件不能超过 20MB')
    return false
  }
  return true
}

function onSuccess() {
  ElMessage.success('上传成功')
  emit('refresh')
}

function onError(err) {
  ElMessage.error('上传失败，请检查文件类型（支持图片、PDF、Office 文档）')
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}
</script>

<style scoped>
.att-list { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.att-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.att-name { color: var(--primary); text-decoration: none; }
.att-name:hover { text-decoration: underline; color: var(--primary-hover); }
.att-size { color: var(--text-muted); font-size: 12px; }
.empty { color: var(--text-muted); font-size: 13px; padding: 8px 0; }
</style>
