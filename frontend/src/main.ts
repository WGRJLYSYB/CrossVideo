/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './assets/main.css'

import App from './App.vue'
import router from './router'

// Apply theme from localStorage (default: dark)
const savedTheme = localStorage.getItem('crossvideo_theme') || 'dark'
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
}

const app = createApp(App)
const pinia = createPinia()

if ((window as any).__CONFIG__?.SENTRY_DSN) {
  import('@sentry/vue').then(Sentry => {
    Sentry.init({
      app,
      dsn: (window as any).__CONFIG__.SENTRY_DSN,
      integrations: [
        Sentry.browserTracingIntegration({ router }),
        Sentry.replayIntegration()
      ],
      tracesSampleRate: 1.0,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0
    });
  });
}

app.use(pinia)
app.use(router)

app.mount('#app')
