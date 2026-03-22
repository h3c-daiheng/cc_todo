import { defineStore } from 'pinia'
import api, { setToken } from '../api/index.js'

export const useUserStore = defineStore('user', {
  state: () => ({ user: null }),
  getters: {
    isLoggedIn: s => !!s.user,
    isAdmin: s => s.user?.is_admin
  },
  actions: {
    async login(username, password) {
      const res = await api.post('/auth/login', { username, password })
      setToken(res.data.access_token)
      this.user = { username }
      return res
    },
    async logout() {
      await api.post('/auth/logout')
      setToken(null)
      this.user = null
    }
  }
})
