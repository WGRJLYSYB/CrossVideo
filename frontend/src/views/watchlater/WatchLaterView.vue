<template>
  <div class="space-y-6">
    <!-- Header & Action Bar -->
    <div class="glass-panel p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <el-input
          v-model="searchQuery"
          placeholder="搜索稍后观看的视频标题或链接..."
          prefix-icon="Search"
          clearable
          class="!w-80"
          @clear="loadData(1)"
          @keyup.enter="loadData(1)"
          id="input-watchlater-search"
        />
        <el-button type="primary" :icon="Search" @click="loadData(1)" id="btn-watchlater-search">
          搜索
        </el-button>
        <el-button :icon="Refresh" @click="resetFilters">
          重置
        </el-button>
      </div>

      <div class="text-xs text-slate-400">
        还有 <span class="font-semibold text-indigo-300">{{ total }}</span> 部待看视频
      </div>
    </div>

    <!-- Data Table Card -->
    <div class="glass-panel rounded-2xl overflow-hidden shadow-xl border border-slate-800">
      <el-table
        :data="items"
        v-loading="loading"
        empty-text="暂无稍后观看视频，标记有趣的视频稍后欣赏吧"
        style="width: 100%"
        class="custom-table"
      >
        <!-- Platform & Title -->
        <el-table-column label="视频内容" min-width="320">
          <template #default="{ row }">
            <div class="py-1">
              <div class="flex items-center gap-2 mb-1.5">
                <PlatformBadge :site-host="row.site_host" />
              </div>
              <a
                :href="row.clean_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors inline-flex items-center gap-1 line-clamp-2"
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

        <!-- Duration & Progress -->
        <el-table-column label="时长 / 进度" width="180">
          <template #default="{ row }">
            <div class="text-xs text-slate-300 font-mono py-1">
              <div>时长: <span class="text-slate-400">{{ formatDuration(row.duration) }}</span></div>
              <div v-if="row.progress_seconds > 0" class="text-indigo-400/90 mt-0.5">
                上次看至: {{ formatDuration(row.progress_seconds) }}
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Added At -->
        <el-table-column label="添加时间" width="180">
          <template #default="{ row }">
            <div class="text-xs text-slate-400 font-mono">
              {{ formatDate(row.created_at) }}
            </div>
          </template>
        </el-table-column>

        <!-- Actions -->
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="flex items-center justify-center gap-2">
              <!-- Favorite Button -->
              <el-tooltip :content="row.is_favorite ? '已收藏' : '转入收藏'" placement="top">
                <el-button
                  size="small"
                  :type="row.is_favorite ? 'warning' : 'default'"
                  plain
                  :icon="row.is_favorite ? StarFilled : Star"
                  circle
                  @click="handleToggleFavorite(row)"
                />
              </el-tooltip>

              <!-- Delete / Remove Button -->
              <el-tooltip content="从稍后观看移除" placement="top">
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
      <div class="p-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="text-xs text-slate-400">
          共 <span class="font-semibold text-slate-200">{{ total }}</span> 条稍后观看
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
import { Search, Refresh, Delete, Star, StarFilled, TopRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PlatformBadge from '@/components/PlatformBadge.vue'
import { getWatchLaterListApi, deleteWatchLaterApi } from '@/api/watchlater'
import { addFavoriteApi } from '@/api/favorites'
import { useAuthStore } from '@/stores/auth'
import { formatDuration, formatDate } from '@/utils/format'
import type { WatchLaterItem } from '@/types'

const authStore = useAuthStore()

const items = ref<WatchLaterItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const searchQuery = ref('')

async function loadData(targetPage = page.value) {
  loading.value = true
  page.value = targetPage
  try {
    const res = await getWatchLaterListApi({
      page: page.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  searchQuery.value = ''
  loadData(1)
}

function handleSizeChange(size: number) {
  pageSize.value = size
  loadData(1)
}

function handleCurrentChange(p: number) {
  loadData(p)
}

async function handleToggleFavorite(row: WatchLaterItem) {
  try {
    await addFavoriteApi({
      clean_url: row.clean_url,
      title: row.title,
      site_host: row.site_host,
      duration: row.duration,
      progress_seconds: row.progress_seconds,
    })
    row.is_favorite = true
    ElMessage.success('已转入我的收藏')
    authStore.fetchProfile()
  } catch {
    // handled by axios interceptor
  }
}

async function handleDelete(row: WatchLaterItem) {
  try {
    await ElMessageBox.confirm(`确定要从稍后观看中移除《${row.title}》吗？`, '移除确认', {
      confirmButtonText: '确定移除',
      cancelButtonText: '暂不',
      type: 'warning',
    })
    await deleteWatchLaterApi(row.id)
    ElMessage.success('已从稍后观看移除')
    loadData()
    authStore.fetchProfile()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  loadData()
})
</script>
