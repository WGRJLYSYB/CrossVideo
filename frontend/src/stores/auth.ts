import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getProfileApi, type LoginParams, type RegisterParams } from '@/api/auth'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('crossvideo_token') || '')
  const username = ref<string>(localStorage.getItem('crossvideo_username') || '')
  const userProfile = ref<UserInfo | null>(null)
  const loading = ref<boolean>(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(params: LoginParams) {
    loading.value = true
    try {
      const res = await loginApi(params)
      token.value = res.access_token
      username.value = res.username
      localStorage.setItem('crossvideo_token', res.access_token)
      localStorage.setItem('crossvideo_username', res.username)
      await fetchProfile()
      return res
    } finally {
      loading.value = false
    }
  }

  async function register(params: RegisterParams) {
    loading.value = true
    try {
      return await registerApi(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    if (!token.value) return null
    try {
      const data = await getProfileApi()
      userProfile.value = data
      return data
    } catch {
      return null
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    userProfile.value = null
    localStorage.removeItem('crossvideo_token')
    localStorage.removeItem('crossvideo_username')
  }

  return {
    token,
    username,
    userProfile,
    loading,
    isAuthenticated,
    login,
    register,
    fetchProfile,
    logout,
  }
})
