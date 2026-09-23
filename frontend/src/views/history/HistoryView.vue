<template>
  <div class="space-y-6">
    <!-- Header & Action Bar -->
    <div class="glass-panel p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <el-input
          v-model="searchQuery"
          placeholder="搜索视频标题或链接..."
          prefix-icon="Search"
          clearable
          class="!w-72"
          @clear="loadData(1)"
          @keyup.enter="loadData(1)"
          id="input-history-search"
        />
        <el-select
          v-model="selectedHost"
          placeholder="全部平台"
          clearable
          class="!w-40"
          @change="loadData(1)"
        >
          <el-option label="全部平台" value="" />
          <el-option label="Bilibili" value="bilibili.com" />
          <el-option label="YouTube" value="youtube.com" />
          <el-option label="腾讯视频" value="v.qq.com" />
          <el-option label="爱奇艺" value="iqiyi.com" />
          <el-option label="优酷" value="youku.com" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="loadData(1)" id="btn-history-search">
          搜索
        </el-button>
        <el-button :icon="Refresh" @click="resetFilters">
          重置
        </el-button>
      </div>

      <div class="flex items-center gap-3">
        <el-button
          type="danger"
          plain
          :icon="Delete"
          :disabled="total === 0"
          @click="handleClearAll"
        >
          清空历史
        </el-button>
      </div>
    </div>

    <!-- Data Table Card -->
    <div class="glass-panel rounded-2xl overflow-hidden shadow-xl border border-slate-800">
      <el-table
        :data="items"
        v-loading="loading"
        empty-text="暂无观看历史记录"
        style="width: 100%"
        class="custom-table"
      >
        <!-- Platform & Title -->
        <el-table-column label="视频内容" min-width="280">
          <template #default="{ row }">
            <div class="py-1">
              <div class="flex items-center gap-2 mb-1.5">
                <PlatformBadge :site-host="row.site_host" />
                <el-tag v-if="row.completed" size="small" type="success" effect="dark" class="!text-xs">
                  已看完
                </el-tag>
              </div>
              <a
                :href="row.clean_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm font-medium text-slate-200 hover:text-indigo-400 transition-colors inline-flex items-center gap-1 line-clamp-2"
                :title="row.title"
              >
                <span>{{ row.title }}</span>
                <el-icon :size="12" class="flex-shrink-0 text-slate-400"><TopRight /></el-icon>
              </a>
              <div class="text-xs text-slate-500 font-mono truncate max-w-md mt-0.5">
                {{ row.clean_url }}
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Progress Bar & Timestamp -->
        <el-table-column label="观看进度" width="230">
          <template #default="{ row }">
            <div class="py-1">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                <span>{{ formatDuration(row.progress_seconds) }} / {{ formatDuration(row.duration) }}</span>
                <span class="font-semibold text-indigo-300">
                  {{ formatProgressPercent(row.progress_seconds, row.duration) }}%
                </span>
              </div>
              <el-progress
                :percentage="formatProgressPercent(row.progress_seconds, row.duration)"
                :status="row.completed ? 'success' : ''"
                :show-text="false"
                :stroke-width="6"
                color="#6366f1"
              />
            </div>
          </template>
        </el-table-column>

        <!-- Updated At -->
        <el-table-column label="最近同步" width="170">
          <template #default="{ row }">
            <div class="text-xs text-slate-400 font-mono">
              {{ formatDate(row.updated_at) }}
            </div>
          </template>
        </el-table-column>

        <!-- Actions -->
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="flex items-center justify-center gap-2">
              <!-- Favorite Button -->
              <el-tooltip :content="row.is_favorite ? '已收藏' : '添加收藏'" placement="top">
                <el-button
                  size="small"
                  :type="row.is_favorite ? 'warning' : 'default'"
                  :icon="row.is_favorite ? StarFilled : Star"
                  circle
                  class="!bg-slate-800 hover:!bg-slate-700 !border-slate-700"
                  @click="handleToggleFavorite(row)"
                />
              </el-tooltip>

              <!-- Watch Later Button -->
              <el-tooltip content="稍后观看" placement="top">
                <el-button
                  size="small"
                  type="default"
                  :icon="CollectionTag"
                  circle
                  class="!bg-slate-800 hover:!bg-slate-700 !border-slate-700"
                  @click="handleAddToWatchLater(row)"
                />
              </el-tooltip>

              <!-- Delete Button -->
              <el-tooltip content="删除此条记录" placement="top">
                <el-button
                  size="small"
                  type="danger"
                  plain
                  :icon="Delete"
                  circle
                  class="hover:!bg-rose-500/20"
                  @click="handleDelete(row)"
                />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination Footer -->
      <div class="p-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/30">
        <div class="text-xs text-slate-400">
          共 <span class="font-semibold text-slate-200">{{ total }}</span> 条播放记录
        </div>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          background
          layout="sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  Search,
  Refresh,
  Delete,
  Star,
  StarFilled,
  CollectionTag,
  TopRight,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { getHistoryListApi, deleteHistoryItemApi, clearHistoryApi } from '@/api/history'
import { addFavoriteApi } from '@/api/favorites'
import { addWatchLaterApi } from '@/api/watchlater'
import { useAuthStore } from '@/stores/auth'
import { formatDuration, formatDate, formatProgressPercent } from '@/utils/format'
import type { HistoryItem } from '@/types'

const authStore = useAuthStore()

const items = ref<HistoryItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const searchQuery = ref('')
const selectedHost = ref('')

async function loadData(targetPage = page.value) {
  loading.value = true
  page.value = targetPage
  try {
    const res = await getHistoryListApi({
      page: page.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      site_host: selectedHost.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  searchQuery.value = ''
  selectedHost.value = ''
  loadData(1)
}

function handleSizeChange(size: number) {
  pageSize.value = size
  loadData(1)
}

function handleCurrentChange(p: number) {
  loadData(p)
}

async function handleToggleFavorite(row: HistoryItem) {
  try {
    await addFavoriteApi({
      clean_url: row.clean_url,
      title: row.title,
      site_host: row.site_host,
      duration: row.duration,
      progress_seconds: row.progress_seconds,
    })
    row.is_favorite = true
    ElMessage.success('已添加到我的收藏')
    authStore.fetchProfile()
  } catch {
    // handled by axios interceptor
  }
}

async function handleAddToWatchLater(row: HistoryItem) {
  try {
    await addWatchLaterApi({
      clean_url: row.clean_url,
      title: row.title,
      site_host: row.site_host,
      duration: row.duration,
      progress_seconds: row.progress_seconds,
    })
    ElMessage.success('已添加到稍后观看')
    authStore.fetchProfile()
  } catch {
    // handled by axios interceptor
  }
}

async function handleDelete(row: HistoryItem) {
  try {
    await ElMessageBox.confirm(`确定要删除历史记录《${row.title}》吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteHistoryItemApi(row.id)
    ElMessage.success('已删除记录')
    loadData()
    authStore.fetchProfile()
  } catch {
    // cancelled
  }
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm('确定要清空所有观看历史记录吗？此操作不可逆！', '高危操作确认', {
      confirmButtonText: '彻底清空',
      cancelButtonText: '取消',
      type: 'error',
    })
    await clearHistoryApi()
    ElMessage.success('历史记录已全部清空')
    loadData(1)
    authStore.fetchProfile()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  loadData()
})
</script>
