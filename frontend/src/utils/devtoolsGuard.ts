/*
CrossVideo — Cross‑platform video playback progress synchronization tool
Copyright (C) 2026 WGRJLYSYB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License v3.0.
See LICENSE file in repository root for full license text.
*/

export async function initializeDevToolsGuard() {
  if (import.meta.env.DEV || import.meta.env.VITE_DISABLE_DEVTOOLS_GUARD === 'true') return
  const { default: devtools } = await import('devtools-detect')

  const overlay = document.createElement('div')
  overlay.setAttribute('role', 'alert')
  overlay.setAttribute('aria-live', 'assertive')
  overlay.style.cssText = [
    'position:fixed',
    'inset:0',
    'z-index:2147483647',
    'display:none',
    'align-items:center',
    'justify-content:center',
    'padding:24px',
    'background:#020617',
    'color:#e2e8f0',
    'font:600 18px/1.6 system-ui,sans-serif',
    'text-align:center',
  ].join(';')
  overlay.textContent = '检测到开发者工具已打开。请关闭开发者工具后继续使用管理后台。'
  document.body.append(overlay)

  const updateOverlay = (isOpen: boolean) => {
    overlay.style.display = isOpen ? 'flex' : 'none'
  }
  window.addEventListener('devtoolschange', (event) => updateOverlay(event.detail.isOpen))
  updateOverlay(devtools.isOpen)
}
