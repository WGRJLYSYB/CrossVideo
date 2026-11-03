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
        <h2 class="text-lg font-semibold">影视观看进度</h2>
        <p class="mt-1 text-xs text-slate-500">按影视名称、季和集汇总跨网站播放进度，最近更新的内容优先显示</p>
      </div>
      <div class="flex gap-2">
        <el-input
          v-model="search"
          clearable
          placeholder="搜索影视名称"
          class="!w-64"
          @keyup.enter="loadData(1)"
          @clear="loadData(1)"
        />
        <el-button :icon="Search" :loading="loading" @click="loadData(1)">搜索</el-button>
      </div>
    </section>

    <section class="glass-panel overflow-hidden rounded-2xl">
      <el-table :data="items" v-loading="loading" empty-text="暂无已识别的影视进度" style="width: 100%">
        <el-table-column label="影视作品" min-width="250">
          <template #default="{ row }">
            <div class="font-medium">{{ row.title }}</div>
            <div class="mt-1 text-xs text-slate-500">第 {{ row.season }} 季 · 第 {{ row.episode }} 集</div>
          </template>
        </el-table-column>
        <el-table-column label="观看进度" min-width="250">
          <template #default="{ row }">
            <div class="mb-1 flex justify-between text-xs text-slate-400">
              <span>{{ formatDuration(row.progress_seconds) }} / {{ formatDuration(row.duration) }}</span>
              <span>{{ formatProgressPercent(row.progress_seconds, row.duration) }}%</span>
            </div>
            <el-progress
              :percentage="formatProgressPercent(row.progress_seconds, row.duration)"
              :status="row.completed ? 'success' : ''"
              :show-text="false"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column label="最近更新" width="190">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.completed" type="success" size="small">已看完</el-tag>
            <el-tag v-else type="info" size="small">观看中</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="flex justify-end border-t border-slate-800/80 p-4">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          background
          layout="total, sizes, prev, pager, next"
          @size-change="loadData(1)"
          @current-change="loadData"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getMediaProgressApi, type MediaProgressItem } from '@/api/mediaProgress'
import { formatDate, formatDuration, formatProgressPercent } from '@/utils/format'

const items = ref<MediaProgressItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const search = ref('')
const loading = ref(false)

async function loadData(targetPage = page.value) {
  if (loading.value) return
  loading.value = true
  page.value = targetPage
  try {
    const result = await getMediaProgressApi({
      page: page.value,
      page_size: pageSize.value,
      search: search.value.trim() || undefined,
    })
    items.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

onMounted(() => void loadData())
</script>
