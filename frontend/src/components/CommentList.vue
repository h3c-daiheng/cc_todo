<template>
  <div class="comment-section">
    <div v-if="comments.length === 0" class="empty">暂无评论</div>
    <div v-for="c in comments" :key="c.id" class="comment">
      <div class="comment-header">
        <span class="author">用户 #{{ c.user_id }}</span>
        <span class="time">{{ formatTime(c.created_at) }}</span>
      </div>
      <p class="content">{{ c.content }}</p>
    </div>
    <div class="comment-input">
      <el-input
        v-model="content"
        type="textarea"
        placeholder="写评论..."
        :rows="3"
        resize="none"
      />
      <el-button type="primary" size="small" @click="submit" :disabled="!content.trim()" style="margin-top:8px">
        发表评论
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const props = defineProps({ taskId: Number, comments: { type: Array, default: () => [] } })
const emit = defineEmits(['refresh'])
const content = ref('')

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function submit() {
  if (!content.value.trim()) return
  try {
    await api.post(`/tasks/${props.taskId}/comments`, { content: content.value })
    content.value = ''
    emit('refresh')
  } catch (e) {
    ElMessage.error('发表评论失败')
  }
}
</script>

<style scoped>
.comment-section { display: flex; flex-direction: column; gap: 12px; }
.empty { color: var(--text-muted); text-align: center; padding: 16px; }
.comment { background: var(--card-inner-bg); border-radius: 8px; padding: 10px 14px; }
.comment-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.author { font-weight: 600; color: var(--primary); font-size: 13px; }
.time { font-size: 12px; color: var(--text-muted); }
.content { color: var(--text-primary); font-size: 14px; }
.comment-input { margin-top: 8px; }
</style>
