/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import apiClient from './client'

export function getBlockedSitesApi(): Promise<{ items: string[] }> {
  return apiClient.get('/blocked-sites')
}

export function addBlockedSiteApi(site_host: string): Promise<{ status: string; site_host: string }> {
  return apiClient.post('/blocked-sites', { site_host })
}

export function removeBlockedSiteApi(site_host: string): Promise<{ status: string; site_host: string }> {
  return apiClient.delete(`/blocked-sites/${encodeURIComponent(site_host)}`)
}
