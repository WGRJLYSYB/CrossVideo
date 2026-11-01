<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <div class="glass-panel w-full max-w-md rounded-2xl border border-slate-800 p-8 text-center">
      <h1 class="text-xl font-semibold text-white">邮箱激活</h1>
      <p class="mt-3 text-sm text-slate-300">{{ message }}</p>
      <router-link :to="authStore.isAuthenticated ? '/settings' : '/login'" class="mt-6 inline-block text-indigo-400">
        {{ authStore.isAuthenticated ? '返回设置' : '前往登录' }}
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { confirmEmailApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const message = ref('正在验证链接…')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    message.value = '激活链接缺少验证令牌。'
    return
  }
  try {
    await confirmEmailApi(token)
    message.value = '邮箱已成功激活。'
  } catch (error: any) {
    message.value = error.response?.data?.detail || '激活链接无效或已过期。'
  }
})
</script>
