<template>
  <div class="task-card" :class="borderClass">
    <div class="card-title">{{ task.title }}</div>
    <div class="card-footer">
      <span class="priority-tag" :class="priorityClass">{{ priorityLabel }}</span>
      <span v-if="task.due_date" class="due">{{ task.due_date }}</span>
    </div>
    <div v-if="task.labels?.length" class="labels">
      <span v-for="l in task.labels" :key="l" class="label-tag">{{ l }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ task: Object })

const priorityMap = {
  high: { cls: 'high', label: '高' },
  medium: { cls: 'medium', label: '中' },
  low: { cls: 'low', label: '低' },
}
const priorityClass = computed(() => priorityMap[props.task.priority]?.cls || 'low')
const priorityLabel = computed(() => priorityMap[props.task.priority]?.label || props.task.priority)

const borderClass = computed(() => {
  if (props.task.status === 'done') return 'border-success'
  if (props.task.status === 'in_progress') return 'border-primary'
  if (props.task.priority === 'high') return 'border-danger'
  if (props.task.priority === 'medium') return 'border-warning'
  return 'border-default'
})
</script>

<style scoped>
.task-card {
  background: var(--card-inner-bg);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
  border-left: 3px solid #CBD5E1;
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s ease;
}
.task-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.border-danger { border-left-color: var(--danger); }
.border-warning { border-left-color: var(--warning); }
.border-primary { border-left-color: var(--primary); }
.border-success { border-left-color: var(--success); }
.border-default { border-left-color: #CBD5E1; }

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.priority-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 9999px;
}
.priority-tag.high { background: #FEE2E2; color: #991B1B; }
.priority-tag.medium { background: #FEF3C7; color: #92400E; }
.priority-tag.low { background: #E0E7FF; color: #3730A3; }

.due { font-size: 11px; color: var(--text-muted); }

.labels { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.label-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--primary-light);
  color: var(--primary);
}
</style>
