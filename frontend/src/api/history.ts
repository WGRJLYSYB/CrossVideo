/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

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
