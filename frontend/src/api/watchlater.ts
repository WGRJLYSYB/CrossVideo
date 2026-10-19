/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import apiClient from './client'
import type { PaginatedResponse, WatchLaterItem } from '@/types'

export interface WatchLaterQueryParams {
  page?: number
  page_size?: number
  search?: string
}

export interface WatchLaterCreateParams {
  clean_url: string
  title: string
  site_host?: string | null
  duration?: number
  progress_seconds?: number
}

export function getWatchLaterListApi(params: WatchLaterQueryParams): Promise<PaginatedResponse<WatchLaterItem>> {
  return apiClient.get('/watchlater', { params })
}

export function addWatchLaterApi(data: WatchLaterCreateParams): Promise<WatchLaterItem> {
  return apiClient.post('/watchlater', data)
}

export function deleteWatchLaterApi(id: number): Promise<{ status: string }> {
  return apiClient.delete(`/watchlater/${id}`)
}
