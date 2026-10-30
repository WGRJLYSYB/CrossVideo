/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

<template>
  <div class="space-y-6" v-loading="loading">
    <div class="grid gap-4 sm:grid-cols-2">
      <section class="glass-panel rounded-2xl p-6">
        <div class="text-sm text-slate-400">在线设备</div>
        <div class="mt-2 text-3xl font-semibold text-indigo-300">{{ dashboard.online_device_count }}</div>
      </section>
      <section class="glass-panel rounded-2xl p-6">
        <div class="text-sm text-slate-400">正在播放</div>
        <div class="mt-2 text-3xl font-semibold text-emerald-300">{{ dashboard.current_videos.length }}</div>
      </section>
    </div>

    <section class="glass-panel rounded-2xl p-6">
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold">各平台观看统计</h3>
          <p class="mt-1 text-xs text-slate-500">按网站统计视频记录数量和累计观看时长</p>
        </div>
        <el-button :icon="Refresh" :loading="loading" :disabled="loading" @click="loadDashboard">刷新</el-button>
      </div>
      <el-empty v-if="dashboard.sites.length === 0" description="暂无观看统计" />
      <div v-else class="space-y-5">
        <article v-for="site in dashboard.sites" :key="site.site_host" class="space-y-2">
          <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
            <div class="min-w-0">
              <span class="font-medium">{{ site.site_name }}</span>
              <span class="ml-2 text-xs text-slate-500">{{ site.site_host }}</span>
            </div>
            <div class="text-xs text-slate-400">
              {{ site.video_count }} 部 · {{ formatDuration(site.watched_seconds) }}
            </div>
          </div>
          <div class="grid gap-1">
            <div class="h-2 overflow-hidden rounded-full bg-slate-800">
              <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${videoPercent(site.video_count)}%` }" />
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-slate-800">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${timePercent(site.watched_seconds)}%` }" />
            </div>
          </div>
        </article>
        <div class="flex gap-4 text-xs text-slate-500">
          <span><i class="mr-1 inline-block h-2 w-2 rounded-full bg-indigo-500" />视频数量</span>
          <span><i class="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-500" />观看时长</span>
        </div>
      </div>
    </section>

    <section class="glass-panel overflow-hidden rounded-2xl">
      <div class="border-b border-slate-800/80 p-5">
        <h3 class="text-lg font-semibold">当前正在播放</h3>
      </div>
      <el-table :data="dashboard.current_videos" empty-text="当前没有设备正在播放" style="width: 100%">
        <el-table-column prop="title" label="视频" min-width="240" show-overflow-tooltip />
        <el-table-column prop="site_host" label="网站" min-width="180" />
        <el-table-column label="设备" min-width="160">
          <template #default="{ row }">{{ row.client_id }}</template>
        </el-table-column>
        <el-table-column label="开始播放时间" width="190">
          <template #default="{ row }">{{ formatDate(row.play_started_at) }}</template>
        </el-table-column>
      </el-table>
      <div class="px-5 pb-4 text-xs text-slate-500">数据由在线油猴脚本心跳提供，页面关闭或心跳超时后设备会下线。</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getDashboardApi, type DashboardData } from '@/api/dashboard'
import { formatDate, formatDuration } from '@/utils/format'

const dashboard = ref<DashboardData>({ online_device_count: 0, current_videos: [], sites: [] })
const loading = ref(false)
const maxVideos = computed(() => Math.max(1, ...dashboard.value.sites.map((site) => site.video_count)))
const maxTime = computed(() => Math.max(1, ...dashboard.value.sites.map((site) => site.watched_seconds)))
let refreshTimer: number | undefined

function videoPercent(count: number) {
  return Math.max(3, (count / maxVideos.value) * 100)
}

function timePercent(seconds: number) {
  return Math.max(3, (seconds / maxTime.value) * 100)
}

async function loadDashboard() {
  if (loading.value) return
  loading.value = true
  try {
    dashboard.value = await getDashboardApi()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadDashboard()
  refreshTimer = window.setInterval(() => void loadDashboard(), 30000)
})

onUnmounted(() => {
  if (refreshTimer !== undefined) window.clearInterval(refreshTimer)
})
</script>
