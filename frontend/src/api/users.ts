import apiClient from './client'

export type UserRole = 'regular' | 'superadmin'

export interface ManagedUser {
  id: number
  username: string
  created_at: string | null
  is_superuser: boolean
  is_active: boolean
}

export interface ManagedUserPage {
  total: number
  page: number
  page_size: number
  items: ManagedUser[]
}

export function getUsersApi(role: UserRole, page: number, pageSize: number): Promise<ManagedUserPage> {
  return apiClient.get('/users', { params: { role, page, page_size: pageSize } })
}

export function updateUserStatusApi(userId: number, isActive: boolean): Promise<{ id: number; is_active: boolean }> {
  return apiClient.patch(`/users/${userId}/status`, { is_active: isActive })
}
