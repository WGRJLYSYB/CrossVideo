/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import apiClient from './client'

export interface MediaProgressItem {
  id: number
  title: string
  season: number
  episode: number
  progress_seconds: number
  duration: number
  updated_at: string
  completed: boolean
}

export interface MediaProgressList {
  total: number
  page: number
  page_size: number
  items: MediaProgressItem[]
}

export function getMediaProgressApi(params: {
  page?: number
  page_size?: number
  search?: string
}): Promise<MediaProgressList> {
  return apiClient.get('/progress/media-list', { params })
}
