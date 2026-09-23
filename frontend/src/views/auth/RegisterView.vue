<template>
  <div class="min-h-screen relative flex items-center justify-center bg-slate-950 px-4 overflow-hidden">
    <!-- Ambient glowing backdrop orbs -->
    <div class="absolute top-1/4 -right-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-1/4 -left-20 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl pointer-events-none"></div>

    <div class="w-full max-w-md relative z-10">
      <!-- Brand Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/30 mb-4">
          <el-icon :size="28" class="text-white"><VideoPlay /></el-icon>
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight font-['Outfit']">CrossVideo 管理后台</h1>
        <p class="text-sm text-slate-400 mt-1">创建新账号开启多端进度同步</p>
      </div>

      <!-- Register Card -->
      <div class="glass-panel rounded-2xl p-8 shadow-2xl border border-slate-800/80">
        <h2 class="text-lg font-semibold text-slate-200 mb-6">注册新用户</h2>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleRegister"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="3-50 个字符（支持英文字母、数字等）"
              size="large"
              prefix-icon="User"
              clearable
              id="input-reg-username"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="至少 8 位，包含英文字母和数字"
              size="large"
              prefix-icon="Lock"
              show-password
              id="input-reg-password"
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="form.confirm_password"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              prefix-icon="Check"
              show-password
              id="input-reg-confirm"
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <div class="mt-8">
            <el-button
              type="primary"
              size="large"
              class="w-full !rounded-xl !h-12 !font-medium !text-base bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 border-0"
              :loading="loading"
              @click="handleRegister"
              id="btn-register"
            >
              完成注册并登录
            </el-button>
          </div>
        </el-form>

        <div class="mt-6 text-center text-sm text-slate-400">
          已有账号？
          <router-link
            to="/login"
            class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors ml-1"
          >
            直接登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirm_password: '',
})

const validateConfirm = (_rule: any, value: string, callback: any) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validatePasswordComplexity = (_rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码长度至少需要 8 个字符'))
  } else if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) {
    callback(new Error('密码必须同时包含英文字母和数字'))
  } else {
    callback()
  }
}

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度需在 3 到 50 个字符之间', trigger: 'blur' },
  ],
  password: [{ required: true, validator: validatePasswordComplexity, trigger: 'blur' }],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
})

async function handleRegister() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.register({
        username: form.username,
        password: form.password,
        confirm_password: form.confirm_password,
      })
      ElMessage.success('注册成功，正在自动登录...')
      await authStore.login({
        username: form.username,
        password: form.password,
      })
      router.push('/history')
    } catch {
      // Error handled by Axios interceptor
    } finally {
      loading.value = false
    }
  })
}
</script>
