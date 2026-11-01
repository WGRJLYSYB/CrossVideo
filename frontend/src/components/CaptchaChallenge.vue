<template>
  <div class="space-y-2" aria-label="人机验证">
    <div class="text-sm text-slate-400">
      按顺序点击：<strong class="text-indigo-300">{{ sequence.join(' → ') || '加载中…' }}</strong>
    </div>
    <div
      v-if="challenge"
      class="relative w-full max-w-[360px] overflow-hidden rounded-lg border border-slate-600 cursor-crosshair select-none"
      @click="handleImageClick"
    >
      <img ref="imageRef" :src="challenge.image" alt="点选验证码" class="block w-full" draggable="false">
      <span
        v-for="(click, index) in clicks"
        :key="index"
        class="absolute flex h-6 w-6 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white bg-indigo-600 text-xs font-bold text-white shadow"
        :style="{ left: `${(click.x / challenge.width) * 100}%`, top: `${(click.y / challenge.height) * 100}%` }"
      >{{ index + 1 }}</span>
    </div>
    <div v-else class="flex h-24 items-center justify-center rounded-lg border border-slate-700 text-sm text-slate-400">
      {{ error || '正在加载验证码…' }}
    </div>
    <div class="flex items-center justify-between text-xs text-slate-500">
      <span>{{ clicks.length }}/2 次点击</span>
      <button type="button" class="text-indigo-400 hover:text-indigo-300" :disabled="loading" @click="refresh">换一张</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getCaptchaApi, type CaptchaChallenge as CaptchaChallengeData, type CaptchaClick } from '@/api/auth'

const challenge = ref<CaptchaChallengeData | null>(null)
const clicks = ref<CaptchaClick[]>([])
const imageRef = ref<HTMLImageElement>()
const loading = ref(false)
const error = ref('')
const sequence = computed(() => challenge.value?.sequence ?? [])

async function refresh() {
  loading.value = true
  error.value = ''
  clicks.value = []
  challenge.value = null
  try {
    challenge.value = await getCaptchaApi()
  } catch {
    error.value = '验证码加载失败，请重试'
  } finally {
    loading.value = false
  }
}

function handleImageClick(event: MouseEvent) {
  if (!challenge.value || !imageRef.value || clicks.value.length >= 2) return
  const bounds = imageRef.value.getBoundingClientRect()
  clicks.value.push({
    x: Math.round(((event.clientX - bounds.left) / bounds.width) * challenge.value.width),
    y: Math.round(((event.clientY - bounds.top) / bounds.height) * challenge.value.height),
  })
}

function getSubmission() {
  if (!challenge.value || clicks.value.length !== 2) return null
  return {
    captcha_id: challenge.value.challenge_id,
    captcha_clicks: clicks.value,
  }
}

defineExpose({ getSubmission, refresh })
onMounted(refresh)
</script>
