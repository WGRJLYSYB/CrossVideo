import apiClient from './client'
import type { HistoryItem, PaginatedResponse } from '@/types'

export interface HistoryQueryParams {
  page?: number
  page_size?: number
  search?: string
  site_host?: string
}

export function getHistoryListApi(params: HistoryQueryParams): Promise<PaginatedResponse<HistoryItem>> {
  return apiClient.get('/history', { params })
}

export function deleteHistoryItemApi(id: number): Promise<{ status: string }> {
  return apiClient.delete(`/history/${id}`)
}

export function clearHistoryApi(): Promise<{ status: string }> {
  return apiClient.delete('/history')
}
