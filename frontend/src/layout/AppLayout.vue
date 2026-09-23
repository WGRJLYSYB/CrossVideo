<template>
  <div class="h-screen flex overflow-hidden" :class="isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-100 text-slate-900'">
    <!-- Left Sidebar — fixed height, independent scroll -->
    <aside
      class="w-64 flex-shrink-0 flex flex-col h-full border-r transition-colors duration-200"
      :class="isDark
        ? 'bg-slate-900/80 border-slate-800/80 backdrop-blur-xl'
        : 'bg-white/90 border-slate-200 backdrop-blur-xl shadow-sm'"
    >
      <!-- Brand Logo — height matches right header h-16 -->
      <div
        class="h-16 px-6 flex items-center gap-3 border-b flex-shrink-0 transition-colors duration-200"
        :class="isDark ? 'border-slate-800/80' : 'border-slate-200'"
      >
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20 flex-shrink-0">
          <el-icon :size="18" class="text-white"><VideoPlay /></el-icon>
        </div>
        <div class="overflow-hidden">
          <div class="text-base font-bold tracking-tight font-['Outfit'] truncate" :class="isDark ? 'text-white' : 'text-slate-800'">CrossVideo</div>
          <div class="text-xs text-indigo-500 font-medium tracking-wide">管理控制台</div>
        </div>
      </div>

      <!-- Navigation Menu — independent scroll -->
      <nav class="flex-1 px-3 py-5 space-y-1 overflow-y-auto min-h-0">
        <router-link
          to="/history"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/history')
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
            : isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'"
          id="nav-history"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="17"><Clock /></el-icon>
            <span>观看历史</span>
          </div>
          <span
            v-if="profile?.history_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/history')
              ? 'bg-indigo-700 text-indigo-100'
              : isDark ? 'bg-slate-800 text-slate-400 group-hover:text-slate-200' : 'bg-slate-200 text-slate-500 group-hover:text-slate-700'"
          >
            {{ profile.history_count }}
          </span>
        </router-link>

        <router-link
          to="/favorites"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/favorites')
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
            : isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'"
          id="nav-favorites"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="17"><Star /></el-icon>
            <span>我的收藏</span>
          </div>
          <span
            v-if="profile?.favorites_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/favorites')
              ? 'bg-indigo-700 text-indigo-100'
              : isDark ? 'bg-slate-800 text-slate-400 group-hover:text-slate-200' : 'bg-slate-200 text-slate-500 group-hover:text-slate-700'"
          >
            {{ profile.favorites_count }}
          </span>
        </router-link>

        <router-link
          to="/watchlater"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/watchlater')
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
            : isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'"
          id="nav-watchlater"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="17"><VideoCamera /></el-icon>
            <span>稍后观看</span>
          </div>
          <span
            v-if="profile?.watch_later_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/watchlater')
              ? 'bg-indigo-700 text-indigo-100'
              : isDark ? 'bg-slate-800 text-slate-400 group-hover:text-slate-200' : 'bg-slate-200 text-slate-500 group-hover:text-slate-700'"
          >
            {{ profile.watch_later_count }}
          </span>
        </router-link>
      </nav>

      <!-- User Profile at bottom -->
      <div
        class="p-4 border-t flex-shrink-0 transition-colors duration-200"
        :class="isDark ? 'border-slate-800/80 bg-slate-900/40' : 'border-slate-200 bg-white/60'"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white shadow-inner flex-shrink-0">
              {{ (authStore.username || 'U')[0].toUpperCase() }}
            </div>
            <div class="truncate">
              <div class="text-sm font-medium truncate" :class="isDark ? 'text-slate-200' : 'text-slate-700'">{{ authStore.username }}</div>
              <div class="text-xs" :class="isDark ? 'text-slate-500' : 'text-slate-400'">已登录</div>
            </div>
          </div>
          <el-tooltip content="退出登录" placement="top">
            <button
              class="p-1.5 rounded-lg transition-colors"
              :class="isDark ? 'text-slate-400 hover:text-rose-400 hover:bg-rose-500/10' : 'text-slate-400 hover:text-rose-500 hover:bg-rose-50'"
              @click="handleLogout"
              id="btn-sidebar-logout"
            >
              <el-icon :size="17"><SwitchButton /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </aside>

    <!-- Main Content Area — independent scroll -->
    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      <!-- Top Navigation Header — h-16 matches sidebar brand height -->
      <header
        class="h-16 px-8 border-b flex items-center justify-between flex-shrink-0 z-20 transition-colors duration-200"
        :class="isDark
          ? 'border-slate-800/80 bg-slate-900/40 backdrop-blur-xl'
          : 'border-slate-200 bg-white/85 backdrop-blur-xl shadow-sm'"
      >
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold font-['Outfit']" :class="isDark ? 'text-white' : 'text-slate-800'">{{ currentTitle }}</h2>
        </div>

        <div class="flex items-center gap-3">
          <!-- Theme Toggle Button -->
          <el-tooltip :content="isDark ? '切换亮色主题' : '切换暗色主题'" placement="bottom">
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200"
              :class="isDark
                ? 'text-slate-400 hover:text-amber-400 hover:bg-amber-400/10'
                : 'text-slate-500 hover:text-indigo-600 hover:bg-indigo-50'"
              @click="toggleTheme"
              id="btn-toggle-theme"
              :aria-label="isDark ? '切换亮色主题' : '切换暗色主题'"
            >
              <el-icon :size="18">
                <Sunny v-if="isDark" />
                <Moon v-else />
              </el-icon>
            </button>
          </el-tooltip>

          <el-dropdown trigger="click" @command="handleCommand">
            <div
              class="flex items-center gap-2 cursor-pointer py-1.5 px-3 rounded-lg transition-colors"
              :class="isDark ? 'hover:bg-slate-800/60' : 'hover:bg-slate-100'"
            >
              <div class="w-7 h-7 rounded-md bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-400">
                {{ (authStore.username || 'U')[0].toUpperCase() }}
              </div>
              <span class="text-sm font-medium" :class="isDark ? 'text-slate-300' : 'text-slate-600'">{{ authStore.username }}</span>
              <el-icon :class="isDark ? 'text-slate-400' : 'text-slate-400'"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="refresh">
                  <el-icon><Refresh /></el-icon>刷新状态
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" class="!text-rose-500">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- View Container — scrollable independently -->
      <main class="flex-1 p-8 overflow-y-auto min-h-0">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const profile = computed(() => authStore.userProfile)
const currentTitle = computed(() => (route.meta.title as string) || '控制台')

// ─── Theme ───────────────────────────────────────────────
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('crossvideo_theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('crossvideo_theme', 'light')
  }
}
// ─────────────────────────────────────────────────────────

function isActive(path: string) {
  return route.path.startsWith(path)
}

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    handleLogout()
  } else if (cmd === 'refresh') {
    authStore.fetchProfile()
    ElMessage.success('统计数据已刷新')
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出当前管理后台登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    authStore.logout()
    ElMessage.success('已安全退出')
    router.push('/login')
  } catch {
    // Cancelled
  }
}

onMounted(() => {
  authStore.fetchProfile()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
