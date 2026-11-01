<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <div class="glass-panel w-full max-w-md rounded-2xl border border-slate-800 p-8">
      <h1 class="text-xl font-semibold text-white">设置新密码</h1>
      <el-form class="mt-6" @submit.prevent="submit">
        <el-form-item label="新密码">
          <el-input v-model="password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="confirmPassword" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-button type="primary" class="w-full" :loading="loading" @click="submit">重置密码</el-button>
      </el-form>
      <router-link to="/login" class="mt-5 block text-center text-sm text-indigo-400">返回登录</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { confirmPasswordResetApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function submit() {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    ElMessage.error('重置链接缺少令牌')
    return
  }
  if (password.value.length < 8 || !/[A-Za-z]/.test(password.value) || !/[0-9]/.test(password.value)) {
    ElMessage.warning('密码至少 8 位，且包含英文字母和数字')
    return
  }
  if (password.value !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await confirmPasswordResetApi({ token, new_password: password.value, confirm_password: confirmPassword.value })
    ElMessage.success('密码已重置，请使用新密码登录')
    await router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>
