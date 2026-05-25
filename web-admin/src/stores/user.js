import { defineStore } from 'pinia'
import { getProfile } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('admin_token') || '',
    user: JSON.parse(localStorage.getItem('admin_user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || 'viewer',
    displayName: (state) => state.user?.display_name || state.user?.username || ''
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('admin_token', token)
    },
    setUser(user) {
      this.user = user
      localStorage.setItem('admin_user', JSON.stringify(user))
    },
    async fetchProfile() {
      try {
        const res = await getProfile()
        if (res.code === 200) {
          this.setUser(res.data)
        }
        return res
      } catch (e) {
        this.clearAuth()
        throw e
      }
    },
    clearAuth() {
      this.token = ''
      this.user = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
    }
  }
})
