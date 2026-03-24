<template>
  <div class="calendar-grid">
    <div v-for="(dayTasks, date) in tasksByDate" :key="date" class="calendar-day">
      <div class="day-header">{{ date }}</div>
      <div class="day-tasks">
        <div v-for="task in dayTasks" :key="task.id" class="task-item">
          {{ task.title }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  }
})

const tasksByDate = computed(() => {
  const grouped = {}
  props.tasks.forEach(task => {
    if (task.due_date) {
      if (!grouped[task.due_date]) {
        grouped[task.due_date] = []
      }
      grouped[task.due_date].push(task)
    }
  })
  return grouped
})
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  padding: 16px;
}

.calendar-day {
  background: var(--card-inner-bg);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid var(--border-color);
}

.day-header {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.day-tasks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-item {
  font-size: 12px;
  color: var(--text-primary);
  padding: 6px;
  background: var(--primary-light);
  border-radius: 4px;
}
</style>
