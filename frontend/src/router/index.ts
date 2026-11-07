/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

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
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/auth/ForgotPasswordView.vue'),
      meta: { requiresAuth: false, title: '找回密码' },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/auth/ResetPasswordView.vue'),
      meta: { requiresAuth: false, title: '重置密码' },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/auth/VerifyEmailView.vue'),
      meta: { requiresAuth: false, title: '邮箱激活' },
    },
    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { requiresAuth: true, title: '仪表盘' },
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('@/views/history/HistoryView.vue'),
          meta: { requiresAuth: true, title: '观看历史' },
        },
        {
          path: 'media-progress',
          name: 'media-progress',
          component: () => import('@/views/MediaProgressView.vue'),
          meta: { requiresAuth: true, title: '影视进度' },
        },
        {
          path: 'watched-sites',
          name: 'watched-sites',
          component: () => import('@/views/WatchedSitesView.vue'),
          meta: { requiresAuth: true, title: '观看过的网站' },
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
        {
          path: 'blocked-sites',
          name: 'blocked-sites',
          component: () => import('@/views/BlockedSitesView.vue'),
          meta: { requiresAuth: true, title: '黑名单管理' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { requiresAuth: true, title: '设置' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/admin/UsersView.vue'),
          meta: { requiresAuth: true, requiresSuperuser: true, title: '用户管理' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  document.title = to.meta.title ? `${to.meta.title} - 葡萄视频管理后台` : '葡萄视频管理后台'

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresSuperuser && authStore.isAuthenticated) {
    if (!authStore.userProfile) await authStore.fetchProfile()
    if (!authStore.userProfile?.is_superuser) return { name: 'dashboard' }
  }
  if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) return { name: 'dashboard' }
  return true
})

export default router
