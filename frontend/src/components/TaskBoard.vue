<template>
  <div class="board">
    <div v-for="col in columns" :key="col.status" class="column">
      <div class="col-header">
        <div class="col-title">
          <span class="dot" :style="{ background: col.color }"></span>
          <span>{{ col.label }}</span>
        </div>
        <span class="col-count">{{ (groupedTasks[col.status] || []).length }}</span>
      </div>
      <draggable
        :list="groupedTasks[col.status] || []"
        group="tasks"
        item-key="id"
        @change="(evt) => onChange(col.status, evt)"
        ghost-class="dragging-ghost"
      >
        <template #item="{ element }">
          <task-card :task="element" @click="$emit('task-click', element)" />
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import draggable from 'vuedraggable'
import TaskCard from './TaskCard.vue'

const props = defineProps({ tasks: Array })
const emit = defineEmits(['update-status', 'task-click'])

const columns = [
  { status: 'pending', label: '待处理', color: '#94A3B8' },
  { status: 'in_progress', label: '进行中', color: '#6366F1' },
  { status: 'done', label: '已完成', color: '#10B981' },
]

const groupedTasks = computed(() => {
  const map = { pending: [], in_progress: [], done: [] }
  for (const t of props.tasks || []) {
    if (map[t.status]) map[t.status].push(t)
  }
  return map
})

function onChange(toStatus, evt) {
  if (evt.added) {
    emit('update-status', { taskId: evt.added.element.id, status: toStatus })
  }
}
</script>

<style scoped>
.board { display: flex; gap: 16px; align-items: flex-start; min-height: 60vh; }
.column {
  flex: 1;
  background: var(--card-bg);
  border-radius: 12px;
  padding: 12px;
  min-height: 200px;
  border: 1px solid var(--border);
}
.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.col-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.col-count {
  font-size: 12px;
  color: var(--text-muted);
}
.dragging-ghost { opacity: 0.4; }
</style>
