<template>
  <div class="min-h-screen relative flex items-center justify-center bg-slate-950 px-4 overflow-hidden">
    <!-- Ambient glowing backdrop orbs -->
    <div class="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none">
    </div>

    <div class="w-full max-w-md relative z-10">
      <!-- Brand Header -->
      <div class="text-center mb-8">
        <div
          class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/30 mb-4">
          <el-icon :size="28" class="text-white">
            <VideoPlay />
          </el-icon>
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight font-['Outfit']">CrossVideo 管理后台</h1>
        <p class="text-sm text-slate-400 mt-1">全平台视频观看进度同步与管理</p>
      </div>

      <!-- Login Card -->
      <div class="glass-panel rounded-2xl p-8 shadow-2xl border border-slate-800/80">
        <h2 class="text-lg font-semibold text-slate-200 mb-6">账号登录</h2>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" prefix-icon="User" clearable
              id="input-username" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock"
              show-password id="input-password" @keyup.enter="handleLogin" />
          </el-form-item>

          <div class="mt-8">
            <el-button type="primary" size="large"
              class="w-full !rounded-xl !h-12 !font-medium !text-base bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 border-0"
              :loading="loading" @click="handleLogin" id="btn-login">
              登录后台
            </el-button>
          </div>
        </el-form>

        <div class="mt-6 text-center text-sm text-slate-400">
          还没有账号？
          <router-link to="/register" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors ml-1">
            立即注册
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
})

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login({
        username: form.username,
        password: form.password,
      })
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/history'
      router.push(redirect)
    } catch (err: any) {
      const status = err.response?.status || err.status
      const msg = err.response?.data?.message || err.message

      switch (status) {
        case 401:
          ElMessage.error('用户名或密码错误')
          break
        case 404:
          ElMessage.error('用户不存在')
          break
        case 429:
          ElMessage.warning('尝试次数过多，请稍后再试')
          break
        case 500:
        case 502:
        case 503:
          ElMessage.error('服务器内部错误，请联系管理员')
          break
        default:
          // 排除网络断开或超时的情况
          if (err.code === 'ECONNABORTED' || !window.navigator.onLine) {
            ElMessage.error('网络连接异常，请检查网络设置')
          } else {
            ElMessage.error(msg || '登录失败，请稍后重试')
          }
          break
      }
    } finally {
      loading.value = false
    }
  })
}
</script>
