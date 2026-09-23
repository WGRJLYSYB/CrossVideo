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
}

export interface FavoriteItem {
  id: number
  site_host: string | null
  clean_url: string
  title: string
  duration: number
  progress_seconds: number
  created_at: string | null
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

export interface TokenResponse {
  access_token: string
  token_type: string
  username: string
}
