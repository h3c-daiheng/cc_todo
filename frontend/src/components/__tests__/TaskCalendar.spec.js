import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskCalendar from '../TaskCalendar.vue'

describe('TaskCalendar', () => {
  it('renders calendar grid', () => {
    const wrapper = mount(TaskCalendar, {
      props: {
        tasks: []
      }
    })
    const grid = wrapper.find('.calendar-grid')
    expect(grid.exists()).toBe(true)
  })

  it('groups tasks by due date', () => {
    const tasks = [
      { id: 1, title: 'Task 1', due_date: '2026-03-24' },
      { id: 2, title: 'Task 2', due_date: '2026-03-24' },
      { id: 3, title: 'Task 3', due_date: '2026-03-25' }
    ]
    const wrapper = mount(TaskCalendar, {
      props: { tasks }
    })
    const tasksByDate = wrapper.vm.tasksByDate
    expect(tasksByDate['2026-03-24']).toHaveLength(2)
    expect(tasksByDate['2026-03-25']).toHaveLength(1)
  })
})
