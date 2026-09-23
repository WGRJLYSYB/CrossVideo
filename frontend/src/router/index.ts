import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false, title: '登录' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresAuth: false, title: '注册' },
    },
    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      redirect: '/history',
      children: [
        {
          path: 'history',
          name: 'history',
          component: () => import('@/views/history/HistoryView.vue'),
          meta: { requiresAuth: true, title: '观看历史' },
        },
        {
          path: 'favorites',
          name: 'favorites',
          component: () => import('@/views/favorites/FavoritesView.vue'),
          meta: { requiresAuth: true, title: '我的收藏' },
        },
        {
          path: 'watchlater',
          name: 'watchlater',
          component: () => import('@/views/watchlater/WatchLaterView.vue'),
          meta: { requiresAuth: true, title: '稍后观看' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/history',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  document.title = to.meta.title ? `${to.meta.title} - CrossVideo` : 'CrossVideo 后台管理'

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
    next({ name: 'history' })
  } else {
    next()
  }
})

export default router
