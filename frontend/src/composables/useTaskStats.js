import { computed } from 'vue'

/**
 * @param {import('vue').Ref<Array>} tasks - reactive array of task objects
 * @param {string} today - ISO date string 'YYYY-MM-DD', defaults to current date
 */
export function useTaskStats(tasks, today = new Date().toISOString().slice(0, 10)) {
  const statusCounts = computed(() => {
    const counts = { pending: 0, in_progress: 0, done: 0 }
    for (const t of tasks.value) {
      if (t.status in counts) counts[t.status]++
    }
    return counts
  })

  const overdueTasks = computed(() =>
    tasks.value.filter(t => t.due_date && t.due_date < today && t.status !== 'done')
  )

  const overdueCount = computed(() => overdueTasks.value.length)

  const priorityCounts = computed(() => {
    const counts = { low: 0, medium: 0, high: 0 }
    for (const t of tasks.value) {
      if (t.priority in counts) counts[t.priority]++
    }
    return counts
  })

  function completionTrend(days = 14) {
    const doneTasks = tasks.value.filter(t => t.status === 'done' && t.updated_at)
    const countsByDate = {}
    for (const t of doneTasks) {
      const d = t.updated_at.slice(0, 10)
      countsByDate[d] = (countsByDate[d] || 0) + 1
    }
    const result = []
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      const dateStr = d.toISOString().slice(0, 10)
      result.push({ date: dateStr, count: countsByDate[dateStr] || 0 })
    }
    return result
  }

  function memberWorkload(members) {
    const openTasks = tasks.value.filter(t => t.status !== 'done')
    const map = {}
    for (const m of members) map[m.user_id] = 0
    for (const t of openTasks) {
      if (t.assigned_to !== null && t.assigned_to in map) {
        map[t.assigned_to]++
      }
    }
    return map
  }

  return { statusCounts, overdueCount, overdueTasks, priorityCounts, completionTrend, memberWorkload }
}
