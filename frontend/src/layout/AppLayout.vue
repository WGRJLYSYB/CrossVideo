<template>
  <div class="min-h-screen flex bg-slate-950 text-slate-100 font-sans">
    <!-- Left Sidebar -->
    <aside class="w-64 flex-shrink-0 bg-slate-900/80 border-r border-slate-800/80 flex flex-col backdrop-blur-xl">
      <!-- Brand Logo -->
      <div class="h-18 px-6 py-5 flex items-center gap-3 border-b border-slate-800/80">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20 flex-shrink-0">
          <el-icon :size="20" class="text-white"><VideoPlay /></el-icon>
        </div>
        <div class="overflow-hidden">
          <div class="text-base font-bold text-white tracking-tight font-['Outfit'] truncate">CrossVideo</div>
          <div class="text-xs text-indigo-400 font-medium tracking-wide">管理控制台</div>
        </div>
      </div>

      <!-- Navigation Menu -->
      <nav class="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        <router-link
          to="/history"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/history') ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'"
          id="nav-history"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="18"><Clock /></el-icon>
            <span>观看历史</span>
          </div>
          <span
            v-if="profile?.history_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/history') ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'"
          >
            {{ profile.history_count }}
          </span>
        </router-link>

        <router-link
          to="/favorites"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/favorites') ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'"
          id="nav-favorites"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="18"><Star /></el-icon>
            <span>我的收藏</span>
          </div>
          <span
            v-if="profile?.favorites_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/favorites') ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'"
          >
            {{ profile.favorites_count }}
          </span>
        </router-link>

        <router-link
          to="/watchlater"
          class="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive('/watchlater') ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'"
          id="nav-watchlater"
        >
          <div class="flex items-center gap-3">
            <el-icon :size="18"><CollectionTag /></el-icon>
            <span>稍后观看</span>
          </div>
          <span
            v-if="profile?.watch_later_count !== undefined"
            class="text-xs px-2 py-0.5 rounded-full font-semibold"
            :class="isActive('/watchlater') ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'"
          >
            {{ profile.watch_later_count }}
          </span>
        </router-link>
      </nav>

      <!-- User Profile at bottom -->
      <div class="p-4 border-t border-slate-800/80 bg-slate-900/40">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-slate-700 to-slate-600 flex items-center justify-center text-sm font-semibold text-white shadow-inner flex-shrink-0">
              {{ (authStore.username || 'U')[0].toUpperCase() }}
            </div>
            <div class="truncate">
              <div class="text-sm font-medium text-slate-200 truncate">{{ authStore.username }}</div>
              <div class="text-xs text-slate-500">已登录</div>
            </div>
          </div>
          <el-tooltip content="退出登录" placement="top">
            <button
              class="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
              @click="handleLogout"
              id="btn-sidebar-logout"
            >
              <el-icon :size="18"><SwitchButton /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top Navigation Header -->
      <header class="h-16 px-8 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40 backdrop-blur-xl sticky top-0 z-20">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold text-white font-['Outfit']">{{ currentTitle }}</h2>
        </div>

        <div class="flex items-center gap-4">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="flex items-center gap-2 cursor-pointer py-1.5 px-3 rounded-lg hover:bg-slate-800/60 transition-colors">
              <div class="w-7 h-7 rounded-md bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xs font-bold text-indigo-300">
                {{ (authStore.username || 'U')[0].toUpperCase() }}
              </div>
              <span class="text-sm text-slate-300 font-medium">{{ authStore.username }}</span>
              <el-icon class="text-slate-400"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="!bg-slate-900 !border-slate-800">
                <el-dropdown-item command="refresh" class="!text-slate-200 hover:!bg-slate-800">
                  <el-icon><Refresh /></el-icon>刷新状态
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" class="!text-rose-400 hover:!bg-rose-500/10">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- View Container -->
      <main class="flex-1 p-8 overflow-y-auto">
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const profile = computed(() => authStore.userProfile)

const currentTitle = computed(() => (route.meta.title as string) || '控制台')

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
      customClass: '!bg-slate-900 !border-slate-800',
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
