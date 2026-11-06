/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

<template>
  <div class="min-h-screen relative flex items-center justify-center px-4 overflow-hidden" :class="isDark ? 'bg-slate-950' : 'bg-slate-100'">
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
        <h1 class="text-2xl font-bold tracking-tight font-['Outfit']" :class="isDark ? 'text-white' : 'text-slate-600'">葡萄管理后台</h1>
        <p class="text-sm text-slate-400 mt-1">全平台视频观看进度同步与管理</p>
      </div>

      <!-- Login Card -->
      <div class="glass-panel rounded-2xl p-8 shadow-2xl border border-slate-800/80">
        <h2 class="text-lg font-semibold mb-6" :class="isDark ? 'text-slate-200' : 'text-slate-600'">账号登录</h2>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
          <el-form-item v-if="!requiresTwoFactor" label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" prefix-icon="User" clearable
              id="input-username" />
          </el-form-item>

          <el-form-item v-if="!requiresTwoFactor" label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock"
              show-password id="input-password" @keyup.enter="handleLogin" />
          </el-form-item>

          <CaptchaChallenge v-if="!requiresTwoFactor" ref="captchaRef" />

          <el-form-item v-else label="验证器验证码" prop="two_factor_code" class="mt-5">
            <el-input
              v-model="form.two_factor_code"
              placeholder="输入身份验证器中的 6 位代码"
              size="large"
              maxlength="8"
              inputmode="numeric"
              autocomplete="one-time-code"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <div class="mt-8">
            <el-button type="primary" size="large"
              class="w-full !rounded-xl !h-12 !font-medium !text-base bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 border-0"
              :loading="loading" @click="handleLogin" id="btn-login">
              {{ requiresTwoFactor ? '验证并登录' : '登录后台' }}
            </el-button>
          </div>
        </el-form>

        <div class="mt-6 text-center text-sm text-slate-400">
          <router-link v-if="!requiresTwoFactor" to="/forgot-password" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            忘记密码？
          </router-link>
          <span v-if="!requiresTwoFactor" class="mx-3">·</span>
          <router-link v-if="!requiresTwoFactor" to="/register" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            立即注册
          </router-link>
          <button v-else class="text-indigo-400 hover:text-indigo-300 font-medium" type="button" @click="cancelTwoFactor">返回账号密码登录</button>
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
import { VideoPlay } from '@element-plus/icons-vue'
import CaptchaChallenge from '@/components/CaptchaChallenge.vue'

const isDark = ref(document.documentElement.classList.contains('dark'))

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const captchaRef = ref<InstanceType<typeof CaptchaChallenge>>()
const requiresTwoFactor = ref(false)
const challengeToken = ref('')

const form = reactive({
  username: '',
  password: '',
  two_factor_code: '',
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
})

async function handleLogin() {
  if (!formRef.value) return
  if (requiresTwoFactor.value) {
    if (!/^\d{6,8}$/.test(form.two_factor_code)) {
      ElMessage.warning('请输入 6-8 位验证器验证码')
      return
    }
    loading.value = true
    try {
      await authStore.completeTwoFactorLogin(challengeToken.value, form.two_factor_code)
      ElMessage.success('登录成功')
      router.push((route.query.redirect as string) || '/history')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '验证器验证码无效')
    } finally {
      loading.value = false
    }
    return
  }
  const captcha = captchaRef.value?.getSubmission()
  if (!captcha) {
    ElMessage.warning('请先按顺序完成图形验证')
    return
  }
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const response = await authStore.login({
        username: form.username,
        password: form.password,
        ...captcha,
      })
      if (response?.requires_2fa && response.challenge_token) {
        requiresTwoFactor.value = true
        challengeToken.value = response.challenge_token
        form.password = ''
        return
      }
      if (response?.access_token) {
        ElMessage.success('登录成功')
        const redirect = (route.query.redirect as string) || '/history'
        router.push(redirect)
        return
      }
    } catch (err: any) {
      const status = err.response?.status || err.status
      const msg = err.response?.data?.detail || err.response?.data?.message || err.message

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
      if (!requiresTwoFactor.value) await captchaRef.value?.refresh()
      loading.value = false
    }
  })
}

function cancelTwoFactor() {
  requiresTwoFactor.value = false
  challengeToken.value = ''
  form.two_factor_code = ''
}
</script>
