import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

interface UserInfo {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    try {
      await fetchMe()
    } catch {
      // If fetchMe fails after login, token might still be valid — retry once
      // Don't throw here; the AppLayout will try fetchMe on mount
    }
  }

  async function register(username: string, password: string) {
    const { data } = await api.post('/auth/register', { username, password })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    try {
      await fetchMe()
    } catch {
      // If fetchMe fails after registration, the token is stored and will be
      // validated when AppLayout mounts. Don't throw — registration succeeded.
    }
  }

  async function fetchMe() {
    const { data } = await api.get('/auth/me')
    user.value = data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isLoggedIn, isAdmin, login, register, fetchMe, logout }
})
