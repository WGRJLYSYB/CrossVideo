import apiClient from './client'

export interface AIMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIChatState {
  messages: AIMessage[]
  month: string
  used_tokens: number
  monthly_token_quota: number
  remaining_tokens: number
  ai_available: boolean
}

export function getAIChatHistoryApi(): Promise<AIChatState> {
  return apiClient.get('/ai/chat/history')
}

type AIChatStreamEvent =
  | { type: 'delta'; content: string }
  | { type: 'done'; answer: string; month: string; used_tokens: number; monthly_token_quota: number; remaining_tokens: number; tokens_used: number }
  | { type: 'error'; message: string }

export async function sendAIChatMessageApi(
  message: string,
  onDelta: (content: string) => void,
): Promise<Omit<AIChatState, 'messages' | 'ai_available'> & { answer: string; tokens_used: number }> {
  const token = localStorage.getItem('crossvideo_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch('/api/v1/admin/ai/chat', {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
  })
  const refreshedToken = response.headers.get('x-access-token')
  if (refreshedToken) localStorage.setItem('crossvideo_token', refreshedToken)
  if (!response.ok) {
    let detail = `AI 请求失败 (${response.status})`
    try {
      const body = await response.json() as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // The response body may not be JSON.
    }
    throw new Error(detail)
  }
  if (!response.body) throw new Error('浏览器不支持读取 AI 流式响应')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result: Extract<AIChatStreamEvent, { type: 'done' }> | undefined

  function dispatch(frame: string) {
    const data = frame
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n')
    if (!data) return
    const event = JSON.parse(data) as AIChatStreamEvent
    if (event.type === 'delta') onDelta(event.content)
    else if (event.type === 'error') throw new Error(event.message)
    else result = event
  }

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    buffer = buffer.replace(/\r\n/g, '\n')
    let boundary = buffer.indexOf('\n\n')
    while (boundary >= 0) {
      dispatch(buffer.slice(0, boundary))
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf('\n\n')
    }
    if (done) {
      if (buffer.trim()) dispatch(buffer)
      break
    }
  }
  if (!result) throw new Error('AI 流式响应意外结束')
  return result
}

export function clearAIChatHistoryApi(): Promise<{ message: string }> {
  return apiClient.delete('/ai/chat/history')
}
