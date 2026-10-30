/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import apiClient from './client'

export interface DashboardData {
  online_device_count: number
  current_videos: {
    client_id: string
    site_host: string | null
    title: string
    play_started_at: string | null
  }[]
  sites: {
    site_host: string
    site_name: string
    video_count: number
    watched_seconds: number
  }[]
}

export function getDashboardApi(): Promise<DashboardData> {
  return apiClient.get('/dashboard')
}
