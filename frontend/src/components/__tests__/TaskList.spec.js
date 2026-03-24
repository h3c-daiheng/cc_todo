import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskList from '../TaskList.vue'

describe('TaskList.vue', () => {
  it('renders task list table with correct columns', () => {
    const tasks = [
      {
        id: 1,
        title: 'Task 1',
        status: 'pending',
        priority: 'high',
        assignee: 'User 1',
        due_date: '2026-03-25'
      },
      {
        id: 2,
        title: 'Task 2',
        status: 'in_progress',
        priority: 'medium',
        assignee: 'User 2',
        due_date: '2026-03-26'
      }
    ]

    const wrapper = mount(TaskList, {
      props: { tasks }
    })

    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.text()).toContain('标题')
    expect(wrapper.text()).toContain('状态')
    expect(wrapper.text()).toContain('优先级')
    expect(wrapper.text()).toContain('负责人')
    expect(wrapper.text()).toContain('截止日期')
    expect(wrapper.text()).toContain('Task 1')
    expect(wrapper.text()).toContain('Task 2')
  })

  it('emits status-change event when status dropdown changes', async () => {
    const tasks = [
      {
        id: 1,
        title: 'Task 1',
        status: 'pending',
        priority: 'high',
        assignee: 'User 1',
        due_date: '2026-03-25'
      }
    ]

    const wrapper = mount(TaskList, {
      props: { tasks }
    })

    const select = wrapper.find('select')
    await select.setValue('in_progress')

    expect(wrapper.emitted('status-change')).toBeTruthy()
    expect(wrapper.emitted('status-change')[0]).toEqual([1, 'in_progress'])
  })
})
