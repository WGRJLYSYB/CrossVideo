/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

<template>
  <div class="space-y-6">
    <section class="glass-panel rounded-2xl p-6">
      <h3 class="mb-2 text-lg font-semibold">黑名单管理</h3>
      <p class="mb-5 text-sm text-slate-400">拉黑网站后会删除该网站现有的观看历史，并忽略之后上报的进度。</p>
      <div class="flex flex-col gap-3 sm:flex-row">
        <el-input
          v-model="siteInput"
          placeholder="输入域名或网址，例如 example.com"
          clearable
          maxlength="2048"
          @keyup.enter="addSite"
        />
        <el-button type="danger" :loading="adding" :disabled="adding || !siteInput.trim()" @click="addSite">
          添加到黑名单
        </el-button>
      </div>
    </section>

    <section class="glass-panel overflow-hidden rounded-2xl">
      <el-table :data="sites" v-loading="loading" empty-text="暂无被拉黑的网站" style="width: 100%">
        <el-table-column label="网站域名" min-width="240">
          <template #default="{ row }">
            <PlatformBadge :site-host="row" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="success"
              plain
              :loading="deletingHost === row"
              :disabled="!!deletingHost && deletingHost !== row"
              @click="unblockSite(row)"
            >
              取消拉黑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="border-t border-slate-800/80 p-4 text-xs text-slate-400">
        共 {{ sites.length }} 个网站
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { addBlockedSiteApi, getBlockedSitesApi, removeBlockedSiteApi } from '@/api/blockedSites'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const sites = ref<string[]>([])
const siteInput = ref('')
const loading = ref(false)
const adding = ref(false)
const deletingHost = ref('')

async function loadSites() {
  loading.value = true
  try {
    const response = await getBlockedSitesApi()
    sites.value = response.items
  } finally {
    loading.value = false
  }
}

async function addSite() {
  if (adding.value || loading.value || !siteInput.value.trim()) return
  adding.value = true
  try {
    const response = await addBlockedSiteApi(siteInput.value.trim())
    siteInput.value = ''
    await loadSites()
    ElMessage.success(`${response.site_host} 已加入黑名单`)
    await authStore.fetchProfile()
  } catch {
    // handled by axios interceptor
  } finally {
    adding.value = false
  }
}

async function unblockSite(host: string) {
  if (deletingHost.value) return
  try {
    await ElMessageBox.confirm(`确定取消对 ${host} 的拉黑吗？`, '取消拉黑确认', {
      confirmButtonText: '取消拉黑',
      cancelButtonText: '保留',
      type: 'warning',
    })
  } catch {
    return
  }
  deletingHost.value = host
  try {
    await removeBlockedSiteApi(host)
    sites.value = sites.value.filter((site) => site !== host)
    ElMessage.success(`${host} 已取消拉黑`)
  } catch {
    // handled by axios interceptor
  } finally {
    deletingHost.value = ''
  }
}

onMounted(loadSites)
</script>
