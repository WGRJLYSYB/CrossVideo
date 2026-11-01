<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div>
      <h1 class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-slate-800'">设置</h1>
      <p class="mt-1 text-sm text-slate-400">管理账号安全和绑定信息</p>
    </div>

    <section class="glass-panel rounded-2xl border p-6" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
      <h2 class="mb-4 text-lg font-semibold">修改密码</h2>
      <el-form label-position="top" @submit.prevent="changePassword">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.current_password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-button type="primary" :loading="passwordLoading" @click="changePassword">更新密码</el-button>
      </el-form>
    </section>

    <section class="glass-panel rounded-2xl border p-6" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
      <h2 class="mb-1 text-lg font-semibold">绑定邮箱</h2>
      <p class="mb-4 text-sm text-slate-400">
        当前状态：{{ settings.pending_email ? `待验证（${settings.pending_email}）` : settings.email_verified ? `已验证（${settings.email}）` : settings.email ? `待验证（${settings.email}）` : '未绑定' }}
      </p>
      <el-button v-if="settings.email_verified && changeEmail" type="primary" @click="changeEmailToggle">更换绑定</el-button>
      <div v-else class="flex flex-col gap-3 sm:flex-row">
        <el-input v-model="email" type="email" placeholder="name@example.com" autocomplete="email" />
        <el-button type="primary" :loading="emailLoading" @click="requestEmail">发送验证链接</el-button>
      </div>
      <p class="mt-3 text-xs text-slate-500">邮箱在点击邮件中的激活链接后才会生效；一个邮箱只能绑定一个账户。</p>
    </section>

    <section class="glass-panel rounded-2xl border p-6" :class="isDark ? 'border-slate-800' : 'border-slate-200'">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold">双因子验证（2FA）</h2>
          <p class="mt-1 text-sm text-slate-400">使用兼容 TOTP 的验证器应用生成动态验证码。</p>
        </div>
        <div class="flex items-center gap-3">
          <el-tag :type="settings.two_factor_enabled ? 'success' : 'info'">
            {{ settings.two_factor_enabled ? '已开启' : '未开启' }}
          </el-tag>
          <el-switch
            :model-value="settings.two_factor_enabled"
            :loading="totpLoading"
            active-text="开启"
            @change="handleTwoFactorToggle"
          />
        </div>
      </div>

      <div v-if="!settings.two_factor_enabled && !totpSetup" class="mt-4 text-sm text-slate-400">
        开启后请使用验证器应用扫描/录入密钥，并完成一次验证码确认。
      </div>
      <div v-if="totpSetup && !settings.two_factor_enabled" class="mt-4 space-y-3">
        <p class="text-sm text-slate-300">在验证器应用中手动添加此密钥：</p>
        <code class="block break-all rounded-lg bg-slate-900/70 p-3 text-sm text-indigo-300">{{ totpSetup.secret }}</code>
        <qrcode-vue :value="totpSetup.provisioning_uri" :size="200" level="H" />
        <div class="flex flex-col gap-3 sm:flex-row">
          <el-input v-model="totpCode" placeholder="输入验证器当前的 6 位代码" inputmode="numeric" maxlength="8" />
          <el-button type="primary" :loading="totpLoading" @click="enableTwoFactor">验证并开启</el-button>
        </div>
      </div>
      <div v-if="settings.two_factor_enabled" class="mt-4 space-y-3">
        <el-button v-if="!showDisableForm" type="danger" plain @click="showDisableForm = true">关闭双因子验证</el-button>
      </div>
      <div v-if="settings.two_factor_enabled && showDisableForm" class="mt-4 space-y-3">
        <el-input v-model="currentPassword" type="password" show-password placeholder="当前账户密码" autocomplete="current-password" />
        <el-input v-model="totpCode" placeholder="验证器验证码" inputmode="numeric" maxlength="8" />
        <div class="flex gap-2">
          <el-button type="danger" plain :loading="totpLoading" @click="disableTwoFactor">确认关闭</el-button>
          <el-button @click="showDisableForm = false">取消</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import QrcodeVue from 'qrcode.vue'
import {
  changePasswordApi,
  disableTwoFactorApi,
  enableTwoFactorApi,
  getAccountSettingsApi,
  requestEmailVerificationApi,
  setupTwoFactorApi,
} from '@/api/auth'

const isDark = ref(document.documentElement.classList.contains('dark'))
const settings = reactive({ email: null as string | null, email_verified: false, pending_email: null as string | null, two_factor_enabled: false })
const passwordForm = reactive({ current_password: '', new_password: '', confirm_password: '' })
const email = ref('')
const changeEmail = ref(true)
const totpCode = ref('')
const currentPassword = ref('')
const totpSetup = ref<{ secret: string; provisioning_uri: string } | null>(null)
const showDisableForm = ref(false)
const passwordLoading = ref(false)
const emailLoading = ref(false)
const totpLoading = ref(false)

async function loadSettings() {
  Object.assign(settings, await getAccountSettingsApi())
  email.value = settings.pending_email || settings.email || ''
}

async function changePassword() {
  if (!passwordForm.current_password || passwordForm.new_password.length < 8) {
    ElMessage.warning('请检查当前密码和新密码长度')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  passwordLoading.value = true
  try {
    await changePasswordApi(passwordForm)
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    ElMessage.success('密码已更新')
  } finally {
    passwordLoading.value = false
  }
}

async function requestEmail() {
  if (!email.value) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  emailLoading.value = true
  try {
    await requestEmailVerificationApi(email.value)
    ElMessage.success('验证邮件已发送，请点击邮件中的链接')
    await loadSettings()
  } finally {
    emailLoading.value = false
  }
}

function changeEmailToggle() {
  changeEmail.value = !changeEmail.value
}

async function beginTwoFactorSetup() {
  totpLoading.value = true
  try {
    totpSetup.value = await setupTwoFactorApi()
  } finally {
    totpLoading.value = false
  }
}

function handleTwoFactorToggle(enabled: string | number | boolean) {
  if (enabled && !settings.two_factor_enabled) {
    beginTwoFactorSetup().catch(() => ElMessage.error('无法开始双因子验证设置'))
  } else if (!enabled && settings.two_factor_enabled) {
    showDisableForm.value = true
  }
}

async function enableTwoFactor() {
  if (!/^\d{6,8}$/.test(totpCode.value)) {
    ElMessage.warning('请输入有效的验证器验证码')
    return
  }
  totpLoading.value = true
  try {
    await enableTwoFactorApi(totpCode.value)
    totpSetup.value = null
    totpCode.value = ''
    await loadSettings()
    showDisableForm.value = false
    ElMessage.success('双因子验证已开启')
  } finally {
    totpLoading.value = false
  }
}

async function disableTwoFactor() {
  if (!currentPassword.value || !/^\d{6,8}$/.test(totpCode.value)) {
    ElMessage.warning('请输入账户密码和有效的验证器验证码')
    return
  }
  totpLoading.value = true
  try {
    await disableTwoFactorApi(currentPassword.value, totpCode.value)
    currentPassword.value = ''
    totpCode.value = ''
    await loadSettings()
    showDisableForm.value = false
    ElMessage.success('双因子验证已关闭')
  } finally {
    totpLoading.value = false
  }
}

onMounted(() => {
  loadSettings().catch(() => ElMessage.error('无法加载账户设置'))
})
</script>
