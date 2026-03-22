<template>
  <div class="task-card" :class="urgentClass">
    <div class="card-title">{{ task.title }}</div>
    <div class="card-meta">
      <el-tag size="small" :type="priorityType">{{ priorityLabel }}</el-tag>
      <span v-if="task.due_date" class="due">{{ task.due_date }}</span>
    </div>
    <div v-if="task.labels?.length" class="labels">
      <el-tag v-for="l in task.labels" :key="l" size="small" class="label-tag">{{ l }}</el-tag>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ task: Object })

const priorityMap = { high: ['danger', '高'], medium: ['warning', '中'], low: ['info', '低'] }
const priorityType = computed(() => priorityMap[props.task.priority]?.[0] || 'info')
const priorityLabel = computed(() => priorityMap[props.task.priority]?.[1] || props.task.priority)

const urgentClass = computed(() => {
  if (!props.task.due_date) return ''
  const diff = (new Date(props.task.due_date) - new Date()) / 86400000
  return diff <= 1 && props.task.status !== 'done' ? 'urgent' : ''
})
</script>

<style scoped>
.task-card {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  border-left: 4px solid #D9D0C7;
  cursor: grab;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.task-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,0.1); }
.task-card.urgent { border-left-color: #E8572A; }
.card-title { font-weight: 600; margin-bottom: 6px; color: #2C2C2C; }
.card-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
.due { color: #E8572A; font-weight: 500; }
.labels { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.label-tag { background: rgba(244,162,89,0.12); border-color: #F4A259; color: #c07020; }
</style>
