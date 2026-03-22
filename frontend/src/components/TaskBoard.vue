<template>
  <div class="board">
    <div v-for="col in columns" :key="col.status" class="column">
      <div class="col-header">
        <span>{{ col.label }}</span>
        <el-badge :value="(groupedTasks[col.status] || []).length" type="info" />
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
  { status: 'pending', label: '待处理' },
  { status: 'in_progress', label: '进行中' },
  { status: 'done', label: '已完成' },
]

const groupedTasks = computed(() => {
  const map = { pending: [], in_progress: [], done: [] }
  for (const t of props.tasks || []) {
    if (map[t.status]) map[t.status].push(t)
  }
  return map
})

function onChange(toStatus, evt) {
  // vuedraggable @change fires with { added: { element, newIndex } } when a card enters a column
  if (evt.added) {
    emit('update-status', { taskId: evt.added.element.id, status: toStatus })
  }
}
</script>

<style scoped>
.board { display: flex; gap: 16px; align-items: flex-start; min-height: 60vh; }
.column {
  flex: 1;
  background: rgba(245,240,235,0.8);
  border-radius: 10px;
  padding: 12px;
  min-height: 200px;
}
.col-header {
  font-weight: 700;
  margin-bottom: 12px;
  font-size: 15px;
  color: #2C2C2C;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dragging-ghost { opacity: 0.4; background: #F4A259; }
</style>
