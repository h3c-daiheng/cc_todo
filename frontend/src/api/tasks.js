import api from './index.js'

/**
 * Fetch all tasks by looping through pages.
 * @param {Object} params - query params (e.g. { team_id: 5 })
 * @returns {Promise<Array>} flat array of all task objects
 */
export async function fetchAllTasks(params = {}) {
  const allTasks = []
  let page = 1
  const size = 100
  while (true) {
    const res = await api.get('/tasks', { params: { ...params, page, size } })
    allTasks.push(...res.data.items)
    if (res.data.items.length < size) break
    page++
  }
  return allTasks
}
