/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

<template>
  <div class="space-y-6">
    <section class="glass-panel flex flex-col gap-4 rounded-2xl p-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold">观看过的网站</h2>
        <p class="mt-1 text-xs text-slate-500">
          网站来自播放历史。延迟测试由浏览器直接发起 HTTPS 请求（网页响应时间，非 ICMP），不经过 CrossVideo 服务器。
        </p>
      </div>
      <el-button
        type="primary"
        :loading="pingingAll"
        :disabled="loading || pingingAll || !!pingingSite || sites.length === 0"
        @click="pingAll"
      >
        全部 Ping
      </el-button>
    </section>

    <section v-loading="loading" class="min-h-32">
      <el-empty v-if="!loading && sites.length === 0" description="暂无观看过的网站" />
      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="site in orderSites"
          :key="site.site_host"
          class="glass-panel rounded-2xl border border-slate-800/80 p-5 transition-colors hover:border-indigo-500/50"
        >
          <a
            :href="siteUrl(site.site_host)"
            target="_blank"
            rel="noopener noreferrer"
            class="block min-h-20"
            :aria-label="`在新标签页打开 ${site.site_name}`"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h3 class="truncate font-semibold card-title">{{ site.site_name || site.site_host }}</h3>
                <p class="mt-1 truncate font-mono text-xs text-slate-400">{{ site.site_host }}</p>
              </div>
              <span class="shrink-0 text-xs text-slate-500">新标签页 ↗</span>
            </div>
            <p class="mt-3 text-xs text-slate-500">最近观看：{{ formatDate(site.last_watched_at) }}</p>
          </a>

          <div class="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-4">
            <span class="text-sm font-bold" :style="{ color: getLatencyColor(site.site_host) }">
              {{ pingLabel(site.site_host) }}
            </span>
            <el-button
              size="small"
              :loading="pingResults[site.site_host]?.state === 'checking'"
              :disabled="loading || pingingAll || !!pingingSite || !siteUrl(site.site_host)"
              @click="pingSite(site.site_host)"
            >
              Ping
            </el-button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { getWatchedSitesApi } from '@/api/watchedSites'
import type { SiteInfo } from '@/types'
import { formatDate } from '@/utils/format'

type PingState = 'checking' | 'success' | 'timeout' | 'failed'
type PingResult = { state: PingState; latency?: number }

const PING_TIMEOUT_MS = 10000
const MAX_CONCURRENT_PINGS = 10
const hostnamePattern = /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$/

const sites = ref<SiteInfo[]>([])
const loading = ref(false)
const pingingAll = ref(false)
const pingingSite = ref('')
const pingResults = ref<Record<string, PingResult>>({})

const orderSites = computed(() => {
  return [...sites.value].sort((a, b) => {
    const aResult = pingResults.value[a.site_host]
    const bResult = pingResults.value[b.site_host]

    if (!aResult && !bResult) return 0
    if (!aResult) return 1
    if (!bResult) return -1

    if (aResult.state === 'checking' && bResult.state !== 'checking') return -1
    if (aResult.state !== 'checking' && bResult.state === 'checking') return 1

    if (aResult.state === 'success' && bResult.state !== 'success') return -1
    if (aResult.state !== 'success' && bResult.state === 'success') return 1

    if (aResult.latency !== undefined && bResult.latency !== undefined) {
      return aResult.latency - bResult.latency
    }

    return 0
  })
})

function siteUrl(host: string): string | undefined {
  const normalizedHost = host.trim().toLowerCase()
  return hostnamePattern.test(normalizedHost) ? `https://${normalizedHost}/` : undefined
}

async function measureLatency(host: string): Promise<PingResult> {
  const baseUrl = siteUrl(host)
  if (!baseUrl) return { state: 'failed' }

  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), PING_TIMEOUT_MS)
  const startedAt = performance.now()
  try {
    await fetch(`${baseUrl}favicon.ico?crossvideo_ping=${Date.now()}`, {
      method: 'GET',
      mode: 'no-cors',
      cache: 'no-store',
      credentials: 'omit',
      signal: controller.signal,
    })
    return { state: 'success', latency: Math.round(performance.now() - startedAt) }
  } catch {
    return { state: controller.signal.aborted ? 'timeout' : 'failed' }
  } finally {
    window.clearTimeout(timeout)
  }
}

function pingLabel(host: string): string {
  const result = pingResults.value[host]
  if (!result) return '尚未测试'
  if (result.state === 'checking') return '测试中…'
  if (result.state === 'timeout') return '请求超时'
  if (result.state === 'failed') return '无法连接'
  return `${result.latency} ms`
}

function getLatencyColor(host: string): string {
  const result = pingResults.value[host]
  if (!result || result.state !== 'success') return 'hsl(0, 0%, 50%)' // 灰色
  const ms = result.latency
  const min = 300;
  const max = 1000;
  if (ms === undefined) return 'hsl(0, 0%, 50%)'; // 灰色
  if (ms < min) return 'hsl(140, 70%, 50%)'; // 绿
  if (ms > max) return 'hsl(0, 70%, 50%)';   // 红
  // 0~1 比例
  const ratio = (ms - min) / (max - min);
  // 色相：140 到 0
  const hue = 140 * (1 - ratio);
  return `hsl(${hue}, 70%, 50%)`;
}

async function pingSite(host: string) {
  if (loading.value || pingingAll.value || pingingSite.value) return
  pingingSite.value = host
  pingResults.value[host] = { state: 'checking' }
  try {
    pingResults.value[host] = await measureLatency(host)
  } finally {
    pingingSite.value = ''
  }
}

async function pingAll() {
  if (loading.value || pingingAll.value || pingingSite.value) return
  pingingAll.value = true
  const queue = sites.value.filter((site) => siteUrl(site.site_host))
  for (const site of queue) pingResults.value[site.site_host] = { state: 'checking' }

  let nextIndex = 0
  try {
    await Promise.all(
      Array.from({ length: Math.min(MAX_CONCURRENT_PINGS, queue.length) }, async () => {
        while (nextIndex < queue.length) {
          const site = queue[nextIndex++]
          pingResults.value[site.site_host] = await measureLatency(site.site_host)
        }
      }),
    )
  } finally {
    pingingAll.value = false
  }
}

async function loadSites() {
  loading.value = true
  try {
    sites.value = await getWatchedSitesApi()
  } finally {
    loading.value = false
  }
}

onMounted(() => void loadSites())
</script>

<style scoped>
.card-title {
    color: var(--el-text-color-regular);
}
</style>