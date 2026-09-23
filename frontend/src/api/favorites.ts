import apiClient from './client'
import type { FavoriteItem, PaginatedResponse } from '@/types'

export interface FavoriteQueryParams {
  page?: number
  page_size?: number
  search?: string
}

export interface FavoriteCreateParams {
  clean_url: string
  title: string
  site_host?: string | null
  duration?: number
  progress_seconds?: number
}

export function getFavoritesListApi(params: FavoriteQueryParams): Promise<PaginatedResponse<FavoriteItem>> {
  return apiClient.get('/favorites', { params })
}

export function addFavoriteApi(data: FavoriteCreateParams): Promise<FavoriteItem> {
  return apiClient.post('/favorites', data)
}

export function deleteFavoriteApi(id: number): Promise<{ status: string }> {
  return apiClient.delete(`/favorites/${id}`)
}
