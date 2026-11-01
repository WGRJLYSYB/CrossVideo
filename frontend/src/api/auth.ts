/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import apiClient from './client'
import type { TokenResponse, UserInfo } from '@/types'

export interface CaptchaClick {
  x: number
  y: number
}

export interface CaptchaSubmission {
  captcha_id: string
  captcha_clicks: CaptchaClick[]
}

export interface CaptchaChallenge {
  challenge_id: string
  image: string
  sequence: string[]
  width: number
  height: number
}

export interface LoginParams extends CaptchaSubmission {
  username: string
  password: string
}

export interface RegisterParams extends CaptchaSubmission {
  username: string
  password: string
  confirm_password: string
}

export interface LoginResponse {
  access_token?: string
  username: string
  requires_2fa: boolean
  challenge_token?: string
}

export function getCaptchaApi(): Promise<CaptchaChallenge> {
  return apiClient.get('/auth/captcha')
}

export function loginApi(data: LoginParams): Promise<LoginResponse> {
  return apiClient.post('/auth/login', data)
}

export function completeTwoFactorLoginApi(challenge_token: string, code: string): Promise<TokenResponse> {
  return apiClient.post('/auth/login/2fa', { challenge_token, code })
}

export function registerApi(data: RegisterParams): Promise<{ message: string }> {
  return apiClient.post('/auth/register', data)
}

export function getProfileApi(): Promise<UserInfo> {
  return apiClient.get('/auth/me')
}

export function getAccountSettingsApi(): Promise<{ email: string | null; email_verified: boolean; pending_email: string | null; two_factor_enabled: boolean }> {
  return apiClient.get('/auth/settings')
}

export function changePasswordApi(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
  return apiClient.post('/auth/password', data)
}

export function requestEmailVerificationApi(email: string): Promise<{ message: string }> {
  return apiClient.post('/auth/email', { email })
}

export function confirmEmailApi(token: string): Promise<{ message: string }> {
  return apiClient.post('/auth/email/confirm', { token })
}

export function setupTwoFactorApi(): Promise<{ secret: string; provisioning_uri: string }> {
  return apiClient.post('/auth/2fa/setup')
}

export function enableTwoFactorApi(code: string): Promise<{ message: string }> {
  return apiClient.post('/auth/2fa/enable', { code })
}

export function disableTwoFactorApi(password: string, code: string): Promise<{ message: string }> {
  return apiClient.post('/auth/2fa/disable', { password, code })
}

export function requestPasswordResetApi(email: string): Promise<{ message: string }> {
  return apiClient.post('/auth/password-reset/request', { email })
}

export function confirmPasswordResetApi(data: { token: string; new_password: string; confirm_password: string }): Promise<{ message: string }> {
  return apiClient.post('/auth/password-reset/confirm', data)
}
