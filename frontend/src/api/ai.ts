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

export function sendAIChatMessageApi(message: string): Promise<AIChatState & { answer: string; tokens_used: number }> {
  return apiClient.post('/ai/chat', { message })
}

export function clearAIChatHistoryApi(): Promise<{ message: string }> {
  return apiClient.delete('/ai/chat/history')
}
