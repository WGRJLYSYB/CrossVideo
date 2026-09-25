// ==UserScript==
// @name         CrossVideo Mobile 跨平台观看进度同步
// @namespace    https://github.com/WGRJLYSYB/CrossVideo/blob/master/tampermonkey/crossvideo-mobile.user.js
// @version      0.1.3
// @description  CrossVideo 移动端浮动按钮版：同步网页视频观看进度
// @author       Gavin Newsom
// @license      MIT
// @match        *://*/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_xmlhttpRequest
// @grant        GM_addValueChangeListener
// @connect      *
// ==/UserScript==

(() => {
    'use strict';

    const DEFAULT_API_BASE = '';
    const TOKEN_KEY = 'crossvideo_access_token';
    const USERNAME_KEY = 'crossvideo_username';
    const API_BASE_KEY = 'crossvideo_api_base';
    const MENU_REVISION_KEY = 'crossvideo_menu_revision';
    const root = document.createElement('div');
    root.id = 'crossvideo-mobile-root';
    document.documentElement.appendChild(root);

    const state = { session: null, timer: null };
    const css = `
        #crossvideo-mobile-root { position: fixed; inset: 0; z-index: 2147483647; pointer-events: none; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18212b; }
        #crossvideo-mobile-root * { box-sizing: border-box; }
        .cv-mobile-fab { position: fixed; top: max(12px, env(safe-area-inset-top)); right: max(12px, env(safe-area-inset-right)); width: 48px; height: 48px; border: 0; border-radius: 50%; background: #FDF6E3; color: #fff; box-shadow: 0 5px 18px rgba(0,0,0,.28); font-size: 22px; pointer-events: auto; cursor: pointer; touch-action: manipulation; }
        .cv-mobile-fab:active { transform: scale(.94); }
        .cv-mobile-overlay { position: fixed; inset: 0; display: grid; align-items: start; justify-items: center; padding: max(76px, calc(env(safe-area-inset-top) + 64px)) 12px 20px; background: rgba(12,18,24,.62); pointer-events: auto; overflow-y: auto; }
        .cv-mobile-card { width: min(460px, 100%); max-height: 82vh; overflow: hidden; padding: 20px; background: #f6f4ed; border: 1px solid #d8d2c4; border-radius: 13px; box-shadow: 0 18px 55px rgba(0,0,0,.32); }
        .cv-mobile-card h2 { margin: 0 0 16px; font: 700 23px/1.1 Georgia, serif; }
        .cv-mobile-close { float: right; border: 0; background: transparent; color: #61706d; font-size: 26px; line-height: 1; padding: 0 4px; }
        .cv-mobile-tabs { display: flex; gap: 8px; margin-bottom: 15px; border-bottom: 1px solid #d8d2c4; }
        .cv-mobile-tabs button { border: 0; background: transparent; color: #61706d; padding: 9px 12px; font-size: 14px; }
        .cv-mobile-tabs button.active { color: #b34a2b; border-bottom: 2px solid #b34a2b; }
        .cv-mobile-field { display: grid; gap: 6px; margin: 11px 0; }
        .cv-mobile-field input, .cv-mobile-search { width: 100%; min-height: 42px; padding: 9px 11px; border: 1px solid #bdb6a8; border-radius: 8px; background: #fffdf8; color: #18212b; font-size: 16px; outline: none; }
        .cv-mobile-field input:focus, .cv-mobile-search:focus { border-color: #b34a2b; box-shadow: 0 0 0 3px rgba(179,74,43,.14); }
        .cv-mobile-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 16px; }
        .cv-mobile-button { min-height: 42px; border: 0; border-radius: 8px; padding: 9px 14px; background: #b34a2b; color: #fff; font-weight: 650; font-size: 15px; }
        .cv-mobile-button.secondary { background: #ddd7ca; color: #18212b; }
        .cv-mobile-error { min-height: 21px; margin-top: 8px; color: #a12f2f; }
        .cv-mobile-toolbar { display: grid; gap: 9px; margin-bottom: 12px; }
        .cv-mobile-filter { display: flex; align-items: center; gap: 8px; color: #61706d; }
        .cv-mobile-list { height: 45vh; overflow-y: auto; overscroll-behavior: contain; padding-right: 4px; }
        .cv-mobile-item { display: flex; align-items: flex-start; gap: 7px; padding: 12px 3px; border-bottom: 1px solid #d8d2c4; cursor: pointer; }
        .cv-mobile-item:active:not(:has(.cv-mobile-delete:active)) { background: rgba(179,74,43,.08); }
        .cv-mobile-main { min-width: 0; flex: 1; }
        .cv-mobile-main a { color: #b34a2b; font-weight: 650; text-decoration: none; }
        .cv-mobile-meta { margin-top: 4px; color: #61706d; font-size: 12px; }
        .cv-mobile-delete { flex: 0 0 auto; border: 0; background: transparent; color: #a12f2f; padding: 3px 5px; font-size: 17px; }
        .cv-mobile-pages { display: flex; justify-content: center; gap: 12px; margin-top: 12px; }
        .cv-mobile-page { width: 42px; height: 38px; border: 1px solid #c9c1b3; border-radius: 8px; background: #fffdf8; color: #b34a2b; font-size: 19px; }
        .cv-mobile-page:disabled { opacity: .35; }
        .cv-mobile-notice { position: fixed; left: 50%; bottom: max(22px, env(safe-area-inset-bottom)); transform: translateX(-50%); padding: 9px 14px; border-radius: 8px; background: rgba(24,33,43,.92); color: #fff; box-shadow: 0 5px 18px rgba(0,0,0,.25); pointer-events: auto; }
        .cv-mobile-toast { position: fixed; width: min(310px, calc(100vw - 30px)); padding: 11px; background: rgba(246,244,237,.92); border-left: 3px solid #b34a2b; border-radius: 8px; box-shadow: 0 6px 22px rgba(0,0,0,.24); pointer-events: auto; }
        .cv-mobile-toast strong { display: block; margin-bottom: 9px; }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    document.documentElement.appendChild(style);

    const token = () => GM_getValue(TOKEN_KEY, '');
    const apiBase = () => `${GM_getValue(API_BASE_KEY, DEFAULT_API_BASE).replace(/\/+$/, '')}/api/v1`;
    const siteHost = () => location.hostname.toLowerCase();
    const request = (method, path, body) => new Promise((resolve, reject) => {
        if (!GM_getValue(API_BASE_KEY, '')) { reject(new Error('请先配置接口地址')); return; }
        const headers = { 'Content-Type': 'application/json' };
        if (token()) headers.Authorization = `Bearer ${token()}`;
        GM_xmlhttpRequest({
            method,
            url: `${apiBase()}${path}`,
            headers,
            data: body ? JSON.stringify(body) : undefined,
            onload: (response) => {
                let data = {};
                try { data = JSON.parse(response.responseText || '{}'); } catch (_) { /* Ignore non-JSON errors. */ }
                if (response.status >= 200 && response.status < 300) resolve(data);
                else reject(new Error(Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join('；') : data.detail || `请求失败（${response.status}）`));
            },
            onerror: () => reject(new Error('无法连接 CrossVideo 服务')),
        });
    });

    const formatTime = (seconds) => {
        const total = Math.max(0, Math.floor(Number(seconds) || 0));
        return [Math.floor(total / 3600), Math.floor((total % 3600) / 60), total % 60].map((part) => String(part).padStart(2, '0')).join(':');
    };
    const cleanUrl = () => {
        const url = new URL(location.href);
        const keep = new URLSearchParams();
        if (url.hostname.includes('youtube.com') && url.searchParams.get('v')) keep.set('v', url.searchParams.get('v'));
        else if (url.hostname.includes('bilibili.com')) ['p', 't'].forEach((key) => { if (url.searchParams.get(key)) keep.set(key, url.searchParams.get(key)); });
        else for (const [key, value] of url.searchParams) if (!/^(utm_|spm_|from|ref|source|vd_source)/i.test(key)) keep.append(key, value);
        url.hash = '';
        url.search = keep.toString();
        return url.toString();
    };
    const sha256 = async (value) => {
        const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
        return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
    };
    const notice = (message) => {
        root.querySelector('.cv-mobile-notice')?.remove();
        const node = document.createElement('div');
        node.className = 'cv-mobile-notice';
        node.textContent = message;
        root.appendChild(node);
        setTimeout(() => node.remove(), 2200);
    };
    const removeToast = () => root.querySelector('.cv-mobile-toast')?.remove();
    const showResumeToast = (progress, video) => {
        removeToast();
        const toast = document.createElement('div');
        toast.className = 'cv-mobile-toast';
        toast.innerHTML = `<strong>检测到上次观看至 ${formatTime(progress)}</strong><button class="cv-mobile-button">跳转恢复</button> <button class="cv-mobile-button secondary">取消（6秒）</button>`;
        const position = () => {
            const bounds = video.getBoundingClientRect();
            toast.style.left = `${bounds.left + bounds.width / 2}px`;
            toast.style.top = `${bounds.top + 10}px`;
            toast.style.transform = 'translateX(-50%)';
        };
        const expiresAt = Date.now() + 6000;
        const countdown = setInterval(() => { toast.querySelector('.secondary').textContent = `取消（${Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000))}秒）`; }, 250);
        let expiry;
        const dismiss = () => { clearInterval(countdown); clearTimeout(expiry); removeToast(); window.removeEventListener('resize', position); window.removeEventListener('scroll', position, true); };
        position();
        window.addEventListener('resize', position);
        window.addEventListener('scroll', position, true);
        toast.querySelector('.cv-mobile-button').onclick = () => { video.currentTime = progress; video.play().catch(() => {}); dismiss(); };
        toast.querySelector('.secondary').onclick = dismiss;
        expiry = setTimeout(dismiss, 6000);
        root.appendChild(toast);
    };
    const closePanel = () => {
        document.body.style.overflow = '';
        document.body.style.position = '';
        root.querySelector('.cv-mobile-overlay')?.remove();
    }
    const openPanel = (html, onReady) => {
        closePanel();
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        root.insertAdjacentHTML('beforeend', `<div class="cv-mobile-overlay"><section class="cv-mobile-card"><button class="cv-mobile-close" type="button">×</button>${html}</section></div>`);
        const overlay = root.querySelector('.cv-mobile-overlay');
        root.querySelector('.cv-mobile-close').onclick = closePanel;
        overlay.onclick = (event) => { if (event.target === overlay) closePanel(); };
        onReady?.(overlay.querySelector('.cv-mobile-card'));
    };

    const showAuth = (mode = 'login') => {
        openPanel(`<h2>CrossVideo</h2><div class="cv-mobile-tabs"><button data-mode="login">登录</button><button data-mode="register">注册</button></div><form><label class="cv-mobile-field">用户名<input name="username" required autocomplete="username"></label><label class="cv-mobile-field">密码<input name="password" type="password" required minlength="8" autocomplete="current-password"></label><label class="cv-mobile-field confirm">确认密码<input name="confirm_password" type="password" minlength="8" autocomplete="new-password"></label><label class="cv-mobile-field">接口地址<input name="api_base" required placeholder="https://example.com"></label><div class="cv-mobile-error"></div><div class="cv-mobile-actions"><button class="cv-mobile-button" type="submit">继续</button></div></form>`, (card) => {
            const tabs = card.querySelectorAll('[data-mode]');
            const form = card.querySelector('form');
            const confirm = card.querySelector('.confirm');
            const error = card.querySelector('.cv-mobile-error');
            form.api_base.value = GM_getValue(API_BASE_KEY, DEFAULT_API_BASE);
            const setMode = (next) => { mode = next; tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.mode === mode)); confirm.style.display = mode === 'register' ? 'grid' : 'none'; };
            tabs.forEach((tab) => { tab.onclick = () => setMode(tab.dataset.mode); });
            setMode(mode);
            form.onsubmit = async (event) => {
                event.preventDefault();
                const data = Object.fromEntries(new FormData(form));
                try {
                    const api = new URL(data.api_base);
                    if (!['http:', 'https:'].includes(api.protocol)) throw new Error('接口地址必须使用 http 或 https');
                    GM_setValue(API_BASE_KEY, data.api_base.replace(/\/+$/, ''));
                    if (mode === 'register') {
                        await request('POST', '/auth/register', data);
                        error.textContent = '注册成功，请使用刚才的账号登录';
                        form.password.value = '';
                        form.confirm_password.value = '';
                        setMode('login');
                        return;
                    }
                    const result = await request('POST', '/auth/login', { username: data.username, password: data.password });
                    GM_setValue(TOKEN_KEY, result.access_token);
                    GM_setValue(USERNAME_KEY, result.username || data.username);
                    closePanel();
                    notice('登录成功');
                    GM_setValue(MENU_REVISION_KEY, Date.now());
                    scan();
                } catch (errorValue) { error.textContent = errorValue.message; }
            };
        });
    };

    const showHistory = async () => {
        if (!token()) { showAuth(); return; }
        openPanel('<h2>播放历史</h2><div class="cv-mobile-toolbar"><input class="cv-mobile-search" type="search" placeholder="搜索标题或网址"><label class="cv-mobile-filter"><input class="site-only" type="checkbox"> 仅当前网站</label></div><div class="cv-mobile-list"></div><div class="cv-mobile-pages"><button class="cv-mobile-page previous" disabled>←</button><button class="cv-mobile-page next" disabled>→</button></div>', (card) => {
            const list = card.querySelector('.cv-mobile-list');
            const searchInput = card.querySelector('.cv-mobile-search');
            const siteOnly = card.querySelector('.site-only');
            const previous = card.querySelector('.previous');
            const next = card.querySelector('.next');
            const pageSize = 5;
            let page = 1;
            let total = null;
            let loading = false;
            let search = '';
            const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
            const updatePages = () => { previous.disabled = loading || page <= 1; next.disabled = loading || page >= Math.ceil((total || 0) / pageSize); };
            const loadPage = async (target) => {
                if (loading || target < 1 || (total !== null && target > Math.ceil(total / pageSize))) return;
                loading = true;
                updatePages();
                try {
                    const filter = siteOnly.checked ? `&site_host=${encodeURIComponent(siteHost())}` : '';
                    const result = await request('GET', `/progress/list?page=${target}&page_size=${pageSize}&search=${encodeURIComponent(search)}${filter}`);
                    total = result.total;
                    list.innerHTML = result.items.map((item) => `<article class="cv-mobile-item" data-url="${escapeHtml(item.clean_url)}" data-id="${item.id}"><div class="cv-mobile-main"><a href="${escapeHtml(item.clean_url)}">${escapeHtml(item.title)}</a><div class="cv-mobile-meta">${formatTime(item.progress_seconds)} / ${formatTime(item.duration)} · ${new Date(item.updated_at).toLocaleString('zh-CN', { hour12: false })}</div></div><button class="cv-mobile-delete">🗑</button></article>`).join('') || '<p>没有找到匹配的播放记录</p>';
                    list.querySelectorAll('.cv-mobile-item').forEach((item) => {
                        item.onclick = (event) => { if (!event.target.closest('button') && !event.target.closest('a')) location.href = item.dataset.url; };
                        item.querySelector('button').onclick = async (event) => { event.stopPropagation(); await request('DELETE', `/progress/records/${item.dataset.id}`); item.remove(); notice('记录已删除'); };
                    });
                    page = target;
                } catch (errorValue) { list.innerHTML = `<p class="cv-mobile-error">${errorValue.message}</p>`; }
                finally { loading = false; updatePages(); }
            };
            previous.onclick = () => loadPage(page - 1);
            next.onclick = () => loadPage(page + 1);
            siteOnly.onchange = () => { page = 1; total = null; loadPage(1); };
            let searchTimer;
            searchInput.oninput = () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { search = searchInput.value.trim(); page = 1; total = null; loadPage(1); }, 750); };
            loadPage(1);
        });
    };

    const sync = async (session) => {
        if (!session || !session.qualified || !token() || !Number.isFinite(session.video.duration)) return;
        try {
            await request('POST', '/progress/sync', { site_host: siteHost(), url_hash: session.urlHash, clean_url: session.cleanUrl, title: document.title || session.cleanUrl, progress_seconds: session.video.currentTime, duration: session.video.duration, client_updated_at: new Date().toISOString() });
        } catch (_) { /* Ignore transient mobile network failures. */ }
    };

    const query = async (session) => {
        if (!session || !token()) return;
        try {
            const result = await request('GET', `/progress/query?url_hash=${session.urlHash}&site_host=${encodeURIComponent(siteHost())}`);
            if (result.found && result.progress_seconds > 0 && result.progress_seconds < session.video.duration * 0.95) showResumeToast(result.progress_seconds, session.video);
        } catch (_) { /* Ignore unavailable resume queries on mobile networks. */ }
    };
    
    const candidate = (video) => video.getBoundingClientRect().width / innerWidth > .5 && Number.isFinite(video.duration) && video.duration > 180;
    const scan = async () => {
        const video = [...document.querySelectorAll('video')].filter(candidate).sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
        if (!video || (state.session?.video === video && state.session.routeUrl === location.href)) return;
        if (state.timer) clearInterval(state.timer);
        const clean = cleanUrl();
        state.session = { video, routeUrl: location.href, cleanUrl: clean, urlHash: await sha256(clean), qualified: false };
        const session = state.session;
        let played = 0;
        video.addEventListener('click', () => { session.qualified = true; });
        video.addEventListener('volumechange', () => { session.qualified = true; });
        video.addEventListener('timeupdate', () => { if (!video.paused) played += .25; if (played >= 10) session.qualified = true; });
        video.addEventListener('pause', () => sync(session));
        video.addEventListener('ended', () => sync(session));
        video.addEventListener('play', () => query(session));
        state.timer = setInterval(() => { if (!video.paused) sync(session); }, 15000);
        await query(session);
    };

    const fab = document.createElement('button');
    fab.className = 'cv-mobile-fab';
    fab.type = 'button';
    fab.textContent = '📽️';
    fab.setAttribute('aria-label', '打开 CrossVideo 菜单');
    fab.title = 'CrossVideo';
    fab.onclick = () => token() ? showHistory() : showAuth();
    root.appendChild(fab);
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    const routeChanged = () => { state.session = null; if (state.timer) clearInterval(state.timer); setTimeout(scan, 500); };
    history.pushState = function (...args) { const result = originalPushState.apply(this, args); routeChanged(); return result; };
    history.replaceState = function (...args) { const result = originalReplaceState.apply(this, args); routeChanged(); return result; };
    addEventListener('popstate', routeChanged);
    addEventListener('beforeunload', () => sync(state.session));
    new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
    document.addEventListener('loadedmetadata', scan, true);
    setTimeout(scan, 800);
})();
