/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

export interface UserInfo {
  id: number
  username: string
  created_at: string | null
  history_count: number
  favorites_count: number
  watch_later_count: number
}

export interface HistoryItem {
  id: number
  site_host: string | null
  clean_url: string
  title: string
  progress_seconds: number
  duration: number
  completed: boolean
  updated_at: string | null
  is_favorite: boolean
  is_watch_later: boolean
}

export interface FavoriteItem {
  id: number
  site_host: string | null
  clean_url: string
  title: string
  duration: number
  progress_seconds: number
  created_at: string | null
  is_watch_later: boolean
}

export interface WatchLaterItem {
  id: number
  site_host: string | null
  clean_url: string
  title: string
  duration: number
  progress_seconds: number
  created_at: string | null
  is_favorite: boolean
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export interface SiteInfo {
  site_host: string
  site_name: string
  last_watched_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  username: string
}
