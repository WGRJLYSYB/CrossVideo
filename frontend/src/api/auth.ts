import apiClient from './client'
import type { TokenResponse, UserInfo } from '@/types'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  confirm_password: string
}

export function loginApi(data: LoginParams): Promise<TokenResponse> {
  return apiClient.post('/auth/login', data)
}

export function registerApi(data: RegisterParams): Promise<{ message: string }> {
  return apiClient.post('/auth/register', data)
}

export function getProfileApi(): Promise<UserInfo> {
  return apiClient.get('/auth/me')
}
