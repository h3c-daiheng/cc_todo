import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../index.js', () => ({
  default: { get: vi.fn() }
}))

import api from '../index.js'
import { fetchAllTasks } from '../tasks.js'

beforeEach(() => vi.clearAllMocks())

describe('fetchAllTasks', () => {
  it('returns all items from a single page response', async () => {
    api.get.mockResolvedValueOnce({
      code: 0, message: 'ok',
      data: { total: 2, page: 1, size: 100, items: [{ id: 1 }, { id: 2 }] }
    })
    const result = await fetchAllTasks()
    expect(result).toHaveLength(2)
    expect(api.get).toHaveBeenCalledTimes(1)
  })

  it('loops through multiple pages until exhausted', async () => {
    const page1 = Array.from({ length: 100 }, (_, i) => ({ id: i + 1 }))
    const page2 = [{ id: 101 }, { id: 102 }, { id: 103 }]
    api.get
      .mockResolvedValueOnce({ code: 0, message: 'ok', data: { total: 103, page: 1, size: 100, items: page1 } })
      .mockResolvedValueOnce({ code: 0, message: 'ok', data: { total: 103, page: 2, size: 100, items: page2 } })
    const result = await fetchAllTasks()
    expect(result).toHaveLength(103)
    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('passes params to each request', async () => {
    api.get.mockResolvedValueOnce({
      code: 0, message: 'ok',
      data: { total: 1, page: 1, size: 100, items: [{ id: 1 }] }
    })
    await fetchAllTasks({ team_id: 5 })
    expect(api.get).toHaveBeenCalledWith('/tasks', { params: { team_id: 5, page: 1, size: 100 } })
  })
})
