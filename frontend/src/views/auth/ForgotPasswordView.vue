<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <div class="glass-panel w-full max-w-md rounded-2xl border border-slate-800 p-8">
      <h1 class="text-xl font-semibold text-white">找回密码</h1>
      <p class="mt-2 text-sm text-slate-400">输入已验证的邮箱，我们会发送密码重置链接。</p>
      <el-form class="mt-6" @submit.prevent="submit">
        <el-form-item label="邮箱">
          <el-input v-model="email" type="email" autocomplete="email" placeholder="name@example.com" />
        </el-form-item>
        <el-button type="primary" class="w-full" :loading="loading" @click="submit">发送重置链接</el-button>
      </el-form>
      <router-link to="/login" class="mt-5 block text-center text-sm text-indigo-400">返回登录</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { requestPasswordResetApi } from '@/api/auth'

const email = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  loading.value = true
  try {
    const result = await requestPasswordResetApi(email.value)
    email.value = ''
    ElMessage.success(result.message)
  } finally {
    loading.value = false
  }
}
</script>
