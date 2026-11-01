<template>
  <el-dialog
    v-model="visible"
    title="CrossVideo 影视讨论"
    width="min(720px, 94vw)"
    :append-to-body="true"
    :close-on-click-modal="false"
    @closed="emit('update:modelValue', false)"
  >
    <div class="space-y-4">
      <div class="flex items-center justify-between gap-3 text-xs text-slate-400">
        <span>{{ state.month }} · 本月已用 {{ state.used_tokens }} / {{ state.monthly_token_quota }} tokens</span>
        <el-button text type="danger" :disabled="messages.length === 0 || busy" @click="clearHistory">清空对话</el-button>
      </div>
      <el-progress
        :percentage="usagePercent"
        :show-text="false"
        :status="state.remaining_tokens === 0 ? 'exception' : undefined"
      />
      <div ref="messageList" class="h-[48vh] min-h-64 space-y-4 overflow-y-auto rounded-xl bg-slate-950/50 p-4">
        <div v-if="!messages.length" class="flex h-full items-center justify-center text-center text-sm text-slate-500">
          可以讨论电影、电视剧、动画的剧情、人物、演员、评价或推荐。
        </div>
        <div
          v-for="(message, index) in messages"
          :key="`${index}-${message.role}`"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[88%] whitespace-pre-wrap break-words rounded-2xl px-4 py-3 text-sm leading-6"
            :class="message.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-200'"
          >{{ message.content }}</div>
        </div>
        <div v-if="busy" class="text-sm text-slate-500">正在思考影视相关内容…</div>
      </div>
      <p v-if="!state.ai_available" class="text-sm text-amber-400">AI 服务尚未配置，请管理员设置 DeepSeek API Key。</p>
      <div class="flex items-end gap-3">
        <el-input
          v-model="draft"
          type="textarea"
          :rows="2"
          resize="none"
          maxlength="4000"
          show-word-limit
          placeholder="输入影视相关问题…"
          :disabled="!state.ai_available || busy || state.remaining_tokens <= 0"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          :loading="busy"
          :disabled="!state.ai_available || busy || state.remaining_tokens <= 0 || !draft.trim()"
          @click="send"
        >发送</el-button>
      </div>
      <p class="text-xs text-slate-500">模型会拒绝非影视话题；本月 token 统计按 DeepSeek 返回的 usage 计算。</p>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  clearAIChatHistoryApi,
  getAIChatHistoryApi,
  sendAIChatMessageApi,
  type AIChatState,
  type AIMessage,
} from '@/api/ai'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const messages = ref<AIMessage[]>([])
const draft = ref('')
const busy = ref(false)
const messageList = ref<HTMLElement>()
const state = reactive<AIChatState>({
  messages: [],
  month: '',
  used_tokens: 0,
  monthly_token_quota: 1000,
  remaining_tokens: 1000,
  ai_available: false,
})
const usagePercent = computed(() => state.monthly_token_quota > 0
  ? Math.min(100, Math.round((state.used_tokens / state.monthly_token_quota) * 100))
  : 0)

async function loadHistory() {
  busy.value = true
  try {
    const result = await getAIChatHistoryApi()
    Object.assign(state, result)
    messages.value = result.messages
    await scrollToBottom()
  } finally {
    busy.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
}

async function send() {
  const content = draft.value.trim()
  if (!content || busy.value || !state.ai_available || state.remaining_tokens <= 0) return
  messages.value.push({ role: 'user', content })
  draft.value = ''
  busy.value = true
  await scrollToBottom()
  try {
    const result = await sendAIChatMessageApi(content)
    messages.value.push({ role: 'assistant', content: result.answer })
    Object.assign(state, result)
  } catch {
    draft.value = content
    messages.value.pop()
  } finally {
    busy.value = false
    await scrollToBottom()
  }
}

async function clearHistory() {
  try {
    await ElMessageBox.confirm('确定清空这段对话记录吗？已用 token 不会退还。', '清空对话', { type: 'warning' })
  } catch {
    return
  }
  try {
    await clearAIChatHistoryApi()
    messages.value = []
    ElMessage.success('对话记录已清空')
  } catch {
    ElMessage.error('清空对话失败')
  }
}

watch(() => props.modelValue, (opened) => {
  if (opened) loadHistory().catch(() => ElMessage.error('无法恢复 AI 对话记录'))
})
</script>
