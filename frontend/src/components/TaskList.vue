<template>
  <table class="task-list">
    <thead>
      <tr>
        <th>标题</th>
        <th>状态</th>
        <th>优先级</th>
        <th>负责人</th>
        <th>截止日期</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="task in tasks" :key="task.id" class="task-row">
        <td class="title-cell">{{ task.title }}</td>
        <td class="status-cell">
          <select :value="task.status" @change="handleStatusChange(task.id, $event)">
            <option value="pending">待处理</option>
            <option value="in_progress">进行中</option>
            <option value="done">已完成</option>
          </select>
        </td>
        <td class="priority-cell">
          <span :class="['priority-badge', task.priority]">{{ priorityLabel(task.priority) }}</span>
        </td>
        <td class="assignee-cell">{{ task.assignee || '-' }}</td>
        <td class="due-date-cell">{{ task.due_date || '-' }}</td>
        <td class="action-cell">
          <button class="detail-btn" @click="$emit('view-detail', task.id)">查看详情</button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
defineProps({
  tasks: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['status-change', 'view-detail'])

const priorityMap = {
  high: '高',
  medium: '中',
  low: '低'
}

const priorityLabel = (priority) => priorityMap[priority] || priority

const handleStatusChange = (taskId, event) => {
  emit('status-change', taskId, event.target.value)
}
</script>

<style scoped>
.task-list {
  width: 100%;
  border-collapse: collapse;
  background: var(--card-inner-bg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

thead {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

tbody tr {
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s ease;
}

tbody tr:hover {
  background-color: var(--bg-hover);
}

td {
  padding: 12px 16px;
  font-size: 13px;
  color: var(--text-primary);
}

.title-cell {
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-cell select {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--card-inner-bg);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
}

.status-cell select:hover {
  border-color: var(--primary);
}

.priority-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.priority-badge.high {
  background: #FEE2E2;
  color: #991B1B;
}

.priority-badge.medium {
  background: #FEF3C7;
  color: #92400E;
}

.priority-badge.low {
  background: #E0E7FF;
  color: #3730A3;
}

.assignee-cell,
.due-date-cell {
  color: var(--text-muted);
}

.action-cell {
  text-align: center;
}

.detail-btn {
  padding: 4px 12px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.detail-btn:hover {
  background: var(--primary-dark);
}
</style>
