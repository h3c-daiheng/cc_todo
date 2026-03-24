import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import QuickTaskInput from '../QuickTaskInput.vue'

describe('QuickTaskInput', () => {
  it('renders input with placeholder', () => {
    const wrapper = mount(QuickTaskInput)
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
    expect(input.attributes('placeholder')).toBe('快速添加任务...')
  })

  it('creates task on enter key', async () => {
    const wrapper = mount(QuickTaskInput, {
      props: {
        onTaskCreate: vi.fn()
      }
    })
    const input = wrapper.find('input')
    await input.setValue('New task')
    await input.trigger('keydown.enter')
    expect(wrapper.vm.inputValue).toBe('')
  })
})
