import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useTaskStats } from '../useTaskStats.js'

const TODAY = '2026-03-23'

describe('useTaskStats', () => {
  it('statusCounts counts tasks by status', () => {
    const tasks = ref([
      { status: 'pending', due_date: null, priority: 'low', updated_at: '2026-03-20T10:00:00' },
      { status: 'in_progress', due_date: null, priority: 'medium', updated_at: '2026-03-21T10:00:00' },
      { status: 'in_progress', due_date: null, priority: 'high', updated_at: '2026-03-22T10:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-23T10:00:00' },
    ])
    const { statusCounts } = useTaskStats(tasks)
    expect(statusCounts.value).toEqual({ pending: 1, in_progress: 2, done: 1 })
  })

  it('overdueCount counts tasks past due_date that are not done', () => {
    const tasks = ref([
      { status: 'pending', due_date: '2026-03-20', priority: 'medium', updated_at: '' },
      { status: 'in_progress', due_date: '2026-03-22', priority: 'medium', updated_at: '' },
      { status: 'done', due_date: '2026-03-20', priority: 'medium', updated_at: '' },
      { status: 'pending', due_date: '2026-03-30', priority: 'medium', updated_at: '' },
      { status: 'pending', due_date: null, priority: 'medium', updated_at: '' },
    ])
    const { overdueCount, overdueTasks } = useTaskStats(tasks, TODAY)
    expect(overdueCount.value).toBe(2)
    expect(overdueTasks.value).toHaveLength(2)
  })

  it('priorityCounts counts tasks by priority', () => {
    const tasks = ref([
      { status: 'pending', due_date: null, priority: 'high', updated_at: '' },
      { status: 'pending', due_date: null, priority: 'high', updated_at: '' },
      { status: 'pending', due_date: null, priority: 'medium', updated_at: '' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '' },
    ])
    const { priorityCounts } = useTaskStats(tasks)
    expect(priorityCounts.value).toEqual({ low: 1, medium: 1, high: 2 })
  })

  it('completionTrend returns counts for done tasks grouped by updated_at date', () => {
    const tasks = ref([
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-22T09:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-22T14:00:00' },
      { status: 'done', due_date: null, priority: 'low', updated_at: '2026-03-23T10:00:00' },
      { status: 'pending', due_date: null, priority: 'low', updated_at: '2026-03-22T10:00:00' },
    ])
    const { completionTrend } = useTaskStats(tasks, TODAY)
    const trend = completionTrend(3)
    expect(trend).toHaveLength(3)
    const march22 = trend.find(d => d.date === '2026-03-22')
    const march23 = trend.find(d => d.date === '2026-03-23')
    const march21 = trend.find(d => d.date === '2026-03-21')
    expect(march22.count).toBe(2)
    expect(march23.count).toBe(1)
    expect(march21.count).toBe(0)
  })

  it('memberWorkload maps userId to open task count', () => {
    const tasks = ref([
      { status: 'pending', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' },
      { status: 'in_progress', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' },
      { status: 'done', assigned_to: 1, due_date: null, priority: 'low', updated_at: '' },
      { status: 'pending', assigned_to: 2, due_date: null, priority: 'low', updated_at: '' },
      { status: 'pending', assigned_to: null, due_date: null, priority: 'low', updated_at: '' },
    ])
    const { memberWorkload } = useTaskStats(tasks)
    const members = [{ user_id: 1 }, { user_id: 2 }, { user_id: 3 }]
    const workload = memberWorkload(members)
    expect(workload[1]).toBe(2)
    expect(workload[2]).toBe(1)
    expect(workload[3]).toBe(0)
  })
})
