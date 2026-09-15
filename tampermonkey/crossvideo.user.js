// ==UserScript==
// @name         CrossVideo 跨平台观看进度同步
// @namespace    https://github.com/crossvideo
// @version      0.1.0
// @description  在不同网站和设备之间同步 HTML5 视频观看进度
// @match        *://*/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_xmlhttpRequest
// @grant        GM_registerMenuCommand
// @grant        GM_unregisterMenuCommand
// @connect      *
// ==/UserScript==

(() => {
    'use strict';

    const DEFAULT_API_BASE = '';
    const TOKEN_KEY = 'crossvideo_access_token';
    const USERNAME_KEY = 'crossvideo_username';
    const API_BASE_KEY = 'crossvideo_api_base';
    const state = {
        activeVideo: null,
        session: null,
        timer: null,
        observer: null,
        routeUrl: location.href,
    };

    const css = `
        #crossvideo-root { position: fixed; z-index: 2147483647; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18212b; }
        #crossvideo-root * { box-sizing: border-box; }
        .cv-overlay { position: fixed; inset: 0; display: grid; align-items: start; justify-items: center; padding: 8vh 20px 20px; background: rgba(12, 18, 24, .62); }
        .cv-card { width: min(440px, 100%); max-height: min(720px, 90vh); overflow: hidden; background: #f6f4ed; border: 1px solid #d8d2c4; border-radius: 12px; box-shadow: 0 20px 70px rgba(0,0,0,.3); padding: 24px; }
        .cv-history-card { max-height: min(720px, 90vh); }
        .cv-card h2 { margin: 0 0 18px; font: 700 24px/1.1 Georgia, serif; }
        .cv-tabs { display: flex; gap: 8px; margin-bottom: 18px; border-bottom: 1px solid #d8d2c4; }
        .cv-tabs button { border: 0; background: transparent; color: #61706d; padding: 9px 12px; cursor: pointer; }
        .cv-tabs button.active { color: #b34a2b; border-bottom: 2px solid #b34a2b; }
        .cv-field { display: grid; gap: 6px; margin: 12px 0; }
        .cv-field input, .cv-search { width: 100%; padding: 10px 11px; border: 1px solid #bdb6a8; border-radius: 7px; background: #fffdf8; color: #18212b; outline: none; transition: border-color .15s, box-shadow .15s; }
        .cv-field input:focus, .cv-search:focus { border-color: #b34a2b; box-shadow: 0 0 0 3px rgba(179, 74, 43, .14); }
        .cv-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 18px; }
        .cv-button { border: 0; border-radius: 6px; padding: 10px 14px; cursor: pointer; background: #b34a2b; color: white; font-weight: 600; }
        .cv-button.secondary { background: #ddd7ca; color: #18212b; }
        .cv-error { color: #a12f2f; min-height: 21px; margin-top: 8px; }
        .cv-toast { position: fixed; width: min(300px, calc(100vw - 36px)); padding: 11px; background: rgba(246, 244, 237, .9); border-left: 3px solid #b34a2b; border-radius: 7px; box-shadow: 0 6px 22px rgba(0,0,0,.22); }
        .cv-toast strong { display: block; margin-bottom: 10px; }
        .cv-history-toolbar { display: grid; gap: 10px; margin-bottom: 14px; }
        .cv-history-filter { display: flex; align-items: center; gap: 8px; color: #61706d; font-size: 13px; }
        .cv-search-wrap { position: relative; }
        .cv-search-wrap .cv-search { padding-right: 36px; }
        .cv-search-clear { position: absolute; top: 50%; right: 8px; transform: translateY(-50%); width: 24px; height: 24px; border: 0; border-radius: 50%; background: transparent; color: #61706d; cursor: pointer; font-size: 18px; line-height: 1; }
        .cv-search-clear:hover { background: #e9e2d7; color: #18212b; }
        .cv-history-list { height: 45vh; overflow-y: auto; overscroll-behavior: contain; padding-right: 6px; scrollbar-width: thin; }
        .cv-history-pagination { display: flex; justify-content: center; gap: 12px; margin-top: 14px; }
        .cv-page-button { width: 38px; height: 34px; border: 1px solid #c9c1b3; border-radius: 7px; background: #fffdf8; color: #b34a2b; cursor: pointer; font-size: 18px; line-height: 1; }
        .cv-page-button:hover:not(:disabled) { background: #f0e8dc; }
        .cv-page-button:disabled { cursor: not-allowed; opacity: .35; }
        .cv-history-item { display: flex; align-items: flex-start; gap: 8px; padding: 13px 4px; border-bottom: 1px solid #d8d2c4; cursor: pointer; }
        .cv-history-item:hover { background: rgba(179, 74, 43, .07); }
        .cv-history-main { min-width: 0; flex: 1; }
        .cv-history-item a { color: #b34a2b; font-weight: 650; text-decoration: none; }
        .cv-delete { flex: 0 0 auto; border: 0; background: transparent; color: #a12f2f; cursor: pointer; font-size: 16px; padding: 2px 5px; }
        .cv-history-meta { color: #61706d; font-size: 12px; margin-top: 4px; }
        .cv-close { float: right; border: 0; background: transparent; font-size: 22px; cursor: pointer; color: #61706d; }
        .cv-history-empty { padding: 22px 4px; color: #61706d; text-align: center; }
        .cv-notice { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); padding: 9px 14px; border-radius: 7px; background: rgba(24, 33, 43, .9); color: #fff; box-shadow: 0 5px 18px rgba(0,0,0,.22); }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    document.documentElement.appendChild(style);

    const root = document.createElement('div');
    root.id = 'crossvideo-root';
    document.documentElement.appendChild(root);

    const token = () => GM_getValue(TOKEN_KEY, '');
    const apiBase = () => `${GM_getValue(API_BASE_KEY, DEFAULT_API_BASE).replace(/\/+$/, '')}/api/v1`;
    const siteHost = () => location.hostname.toLowerCase();
    const requestErrorMessage = (data, status) => {
        if (Array.isArray(data.detail)) {
            return data.detail.map((item) => `${item.loc?.at(-1) || '请求'}: ${item.msg}`).join('；');
        }
        return data.detail || `请求失败（${status}）`;
    };
    const request = (method, path, body) => new Promise((resolve, reject) => {
        if (!GM_getValue(API_BASE_KEY, '')) { reject(new Error('请先在登录窗口填写接口地址')); return; }
        const headers = { 'Content-Type': 'application/json' };
        if (token()) headers.Authorization = `Bearer ${token()}`;
        GM_xmlhttpRequest({
            method,
            url: `${apiBase()}${path}`,
            headers,
            data: body ? JSON.stringify(body) : undefined,
            onload: (response) => {
                let data;
                try { data = JSON.parse(response.responseText || '{}'); } catch (_) { data = {}; }
                if (response.status >= 200 && response.status < 300) resolve(data);
                else reject(new Error(requestErrorMessage(data, response.status)));
            },
            onerror: () => reject(new Error('无法连接 CrossVideo 服务')),
        });
    });

    const formatTime = (seconds) => {
        const total = Math.max(0, Math.floor(Number(seconds) || 0));
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor((total % 3600) / 60);
        const remainder = total % 60;
        return [hours, minutes, remainder].map((part) => String(part).padStart(2, '0')).join(':');
    };

    const cleanUrl = () => {
        const url = new URL(location.href);
        const keep = new URLSearchParams();
        const host = url.hostname.toLowerCase();
        if (host.includes('youtube.com')) {
            if (url.searchParams.get('v')) keep.set('v', url.searchParams.get('v'));
        } else if (host.includes('bilibili.com')) {
            for (const key of ['p', 't']) if (url.searchParams.get(key)) keep.set(key, url.searchParams.get(key));
        } else {
            for (const [key, value] of url.searchParams) {
                if (!/^(utm_|spm_|from|ref|source|vd_source)/i.test(key)) keep.append(key, value);
            }
        }
        url.hash = '';
        url.search = keep.toString();
        return url.toString();
    };

    const sha256 = async (value) => {
        const bytes = new TextEncoder().encode(value);
        const digest = await crypto.subtle.digest('SHA-256', bytes);
        return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
    };

    const removeToast = () => {
        root.querySelector('.cv-toast')?.remove();
    };

    const showNotice = (message) => {
        root.querySelector('.cv-notice')?.remove();
        const notice = document.createElement('div');
        notice.className = 'cv-notice';
        notice.textContent = message;
        root.appendChild(notice);
        window.setTimeout(() => notice.remove(), 2200);
    };

    const showToast = (progress, duration, video, session) => {
        removeToast();
        const toast = document.createElement('div');
        toast.className = 'cv-toast';
        toast.innerHTML = `<strong>💡 检测到您上次观看至 ${formatTime(progress)}</strong><button class="cv-button">跳转恢复</button> <button class="cv-button secondary">取消（6秒）</button>`;
        const positionToast = () => {
            const bounds = video.getBoundingClientRect();
            toast.style.left = `${bounds.left + bounds.width / 2}px`;
            toast.style.top = `${bounds.top + 10}px`;
            toast.style.transform = 'translateX(-50%)';
        };
        positionToast();
        window.addEventListener('resize', positionToast);
        window.addEventListener('scroll', positionToast, true);
        const cancelButton = toast.querySelector('.secondary');
        const expiresAt = Date.now() + 6000;
        const countdown = window.setInterval(() => {
            const remaining = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
            cancelButton.textContent = `取消（${remaining}秒）`;
        }, 250);
        let expirationTimer;
        const dismiss = () => {
            window.clearInterval(countdown);
            window.clearTimeout(expirationTimer);
            window.removeEventListener('resize', positionToast);
            window.removeEventListener('scroll', positionToast, true);
            toast.remove();
        };
        const cancel = () => {
            dismiss();
        };
        cancelButton.onclick = cancel;
        root.appendChild(toast);
        toast.querySelector('.cv-button').onclick = () => {
            video.currentTime = progress;
            video.play().catch(() => {});
            dismiss();
            session.restored = true;
        };
        expirationTimer = window.setTimeout(dismiss, 6000);
    };

    const isCandidate = (video) => {
        const fullScreen = document.fullscreenElement === video || video.webkitDisplayingFullscreen;
        const largeEnough = video.getBoundingClientRect().width / window.innerWidth > 0.5 || fullScreen;
        return largeEnough && Number.isFinite(video.duration) && video.duration > 180;
    };

    const sync = async (session) => {
        if (!session || !session.qualified || !token() || !Number.isFinite(session.video.duration)) return;
        try {
            await request('POST', '/progress/sync', {
                site_host: siteHost(),
                url_hash: session.urlHash,
                clean_url: session.cleanUrl,
                title: document.title || session.cleanUrl,
                progress_seconds: session.video.currentTime,
                duration: session.video.duration,
                client_updated_at: new Date().toISOString(),
            });
        } catch (_) { /* A later timer or pause event retries the update. */ }
    };

    const startSession = async (video) => {
        if (state.session?.video === video && state.session.routeUrl === location.href) return;
        if (state.timer) window.clearInterval(state.timer);
        removeToast();
        state.activeVideo = video;
        const url = cleanUrl();
        const session = { video, routeUrl: location.href, cleanUrl: url, urlHash: await sha256(url), interacted: false, playedSeconds: 0, qualified: false, restored: false };
        state.session = session;
        const markInteraction = () => { session.interacted = true; };
        video.addEventListener('click', markInteraction, { once: false });
        video.addEventListener('volumechange', markInteraction, { once: false });
        video.addEventListener('timeupdate', () => {
            if (!video.paused) session.playedSeconds += 0.25;
            if (isCandidate(video) && (session.interacted || session.playedSeconds >= 10)) session.qualified = true;
        });
        video.addEventListener('pause', () => sync(session));
        video.addEventListener('ended', () => sync(session));
        state.timer = window.setInterval(() => {
            if (!session.video.paused) sync(session);
        }, 15000);
        if (!token() || !isCandidate(video)) return;
        try {
            const result = await request('GET', `/progress/query?url_hash=${session.urlHash}&site_host=${encodeURIComponent(siteHost())}`);
            if (result.found && result.progress_seconds > 0 && result.progress_seconds < video.duration * 0.95) showToast(result.progress_seconds, video.duration, video, session);
        } catch (_) { /* Anonymous or offline pages remain usable. */ }
    };

    const scan = () => {
        const videos = [...document.querySelectorAll('video')].filter(isCandidate);
        if (videos.length) startSession(videos.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0]);
    };

    const showModal = (content, cardClass = '') => {
        root.innerHTML = `<div class="cv-overlay"><section class="cv-card ${cardClass}"><button class="cv-close" aria-label="关闭">×</button>${content}</section></div>`;
        const overlay = root.querySelector('.cv-overlay');
        const close = () => { root.innerHTML = ''; };
        root.querySelector('.cv-close').onclick = close;
        overlay.onclick = (event) => { if (event.target === overlay) close(); };
    };

    const showAuth = (mode = 'login') => {
        showModal(`<h2>CrossVideo</h2><div class="cv-tabs"><button data-mode="login">登录</button><button data-mode="register">注册</button></div><form><label class="cv-field">用户名<input name="username" required autocomplete="username"></label><label class="cv-field">密码<input name="password" type="password" required minlength="8" autocomplete="new-password"></label><label class="cv-field confirm-field">确认密码<input name="confirm_password" type="password" minlength="8" autocomplete="new-password"></label><label class="cv-field">接口地址<input name="api_base" value="${GM_getValue(API_BASE_KEY, DEFAULT_API_BASE)}" placeholder="http://127.0.0.1:8000" required></label><div class="cv-error"></div><div class="cv-actions"><button class="cv-button" type="submit">继续</button></div></form>`);
        const tabs = root.querySelectorAll('[data-mode]');
        const form = root.querySelector('form');
        const confirm = root.querySelector('.confirm-field');
        const error = root.querySelector('.cv-error');
        const setMode = (next) => { mode = next; tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.mode === mode)); confirm.style.display = mode === 'register' ? 'grid' : 'none'; };
        tabs.forEach((tab) => { tab.onclick = () => setMode(tab.dataset.mode); });
        setMode(mode);
        form.onsubmit = async (event) => {
            event.preventDefault();
            const data = Object.fromEntries(new FormData(form));
            try {
                if (!data.api_base.trim()) throw new Error('请填写接口地址');
                const parsedApiBase = new URL(data.api_base);
                if (!['http:', 'https:'].includes(parsedApiBase.protocol)) throw new Error('接口地址必须使用 http 或 https');
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
                root.innerHTML = '';
                registerMenus();
                showNotice('登录成功');
                scan();
            } catch (requestError) { error.textContent = requestError.message; }
        };
    };

    const showHistory = async () => {
        if (!token()) { showAuth(); return; }
        showModal('<h2>播放历史</h2><div class="cv-history-toolbar"><div class="cv-search-wrap"><input class="cv-search" type="search" placeholder="搜索标题或网址" aria-label="搜索播放历史"><button class="cv-search-clear" type="button" aria-label="清空搜索">×</button></div><label class="cv-history-filter"><input class="cv-site-only" type="checkbox"> 仅当前网站</label></div><div class="cv-history-list"></div><div class="cv-history-pagination"><button class="cv-page-button previous" type="button" aria-label="上一页" disabled>←</button><button class="cv-page-button next" type="button" aria-label="下一页" disabled>→</button></div>', 'cv-history-card');
        const list = root.querySelector('.cv-history-list');
        const searchInput = root.querySelector('.cv-search');
        const searchClear = root.querySelector('.cv-search-clear');
        const siteOnly = root.querySelector('.cv-site-only');
        const previousButton = root.querySelector('.cv-page-button.previous');
        const nextButton = root.querySelector('.cv-page-button.next');
        const pageSize = 5;
        let page = 1;
        let total = null;
        let loading = false;
        let search = '';

        const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));

        const updatePagination = () => {
            const totalPages = total === null ? 0 : Math.ceil(total / pageSize);
            previousButton.disabled = loading || page <= 1;
            nextButton.disabled = loading || page >= totalPages;
        };

        const loadPage = async (targetPage) => {
            if (loading || targetPage < 1 || (total !== null && targetPage > Math.ceil(total / pageSize))) return;
            loading = true;
            updatePagination();
            try {
                const siteQuery = siteOnly.checked ? `&site_host=${encodeURIComponent(siteHost())}` : '';
                const result = await request('GET', `/progress/list?page=${targetPage}&page_size=${pageSize}&search=${encodeURIComponent(search)}${siteQuery}`);
                total = result.total;
                const items = result.items.map((item) => `<article class="cv-history-item" data-id="${item.id}" data-url="${escapeHtml(item.clean_url)}"><div class="cv-history-main"><a href="${escapeHtml(item.clean_url)}">${escapeHtml(item.title)}</a><div class="cv-history-meta">${formatTime(item.progress_seconds)} / ${formatTime(item.duration)} · ${new Date(item.updated_at).toLocaleString('zh-CN', { hour12: false })}</div></div><button class="cv-delete" type="button" aria-label="删除记录">🗑</button></article>`).join('');
                list.innerHTML = items || '<p class="cv-history-empty">没有找到匹配的播放记录</p>';
                list.querySelectorAll('.cv-history-item').forEach((item) => {
                    item.onclick = (event) => {
                        if (event.target.closest('.cv-delete') || event.target.closest('a')) return;
                        location.href = item.dataset.url;
                    };
                    item.querySelector('.cv-delete').onclick = async (event) => {
                        event.stopPropagation();
                        await request('DELETE', `/progress/records/${item.dataset.id}`);
                        item.remove();
                    };
                });
                page = targetPage;
            } catch (error) {
                list.innerHTML = `<p class="cv-error">${error.message}</p>`;
            } finally {
                loading = false;
                updatePagination();
            }
        };

        previousButton.onclick = () => loadPage(page - 1);
        nextButton.onclick = () => loadPage(page + 1);
        siteOnly.onchange = () => { page = 1; total = null; loadPage(1); };
        searchClear.onclick = () => {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            searchInput.focus();
        };
        let searchTimer;
        searchInput.addEventListener('input', () => {
            window.clearTimeout(searchTimer);
            searchTimer = window.setTimeout(() => {
                search = searchInput.value.trim();
                page = 1;
                total = null;
                loadPage(1);
            }, 750);
        });
        await loadPage(1);
    };

    let menuIds = [];
    let menuVersion = 0;
    const logout = () => {
        GM_setValue(TOKEN_KEY, '');
        GM_setValue(USERNAME_KEY, '');
        root.innerHTML = '';
        showNotice('已退出登录');
        registerMenus();
    };
    const toggleBlockedSite = async () => {
        if (!token()) { showAuth(); return; }
        try {
            const result = await request('GET', '/progress/blocked-sites');
            const blocked = result.items.includes(siteHost());
            if (blocked) {
                await request('DELETE', `/progress/blocked-sites/${encodeURIComponent(siteHost())}`);
                showNotice('已解除当前网站黑名单');
            } else {
                await request('POST', '/progress/blocked-sites', { site_host: siteHost() });
                showNotice('已拉黑当前网站，并删除该网站历史记录');
            }
            registerMenus();
        } catch (error) { showNotice(error.message); }
    };
    const registerMenus = async () => {
        const version = ++menuVersion;
        menuIds.filter((id) => id !== undefined).forEach((id) => {
            try { GM_unregisterMenuCommand(id); } catch (_) { /* Older managers may not support unregistering. */ }
        });
        menuIds = [];
        const username = GM_getValue(USERNAME_KEY, '');
        const loggedIn = Boolean(token());
        const accountLabel = loggedIn ? `👤 ${username.slice(0, 5) || '已登录'}（退出）` : '🔑 登录 / 注册账号';
        menuIds.push(GM_registerMenuCommand(accountLabel, loggedIn ? logout : () => showAuth()));
        menuIds.push(GM_registerMenuCommand('📜 查看播放历史', showHistory));
        if (loggedIn) {
            let blocked = false;
            try { blocked = (await request('GET', '/progress/blocked-sites')).items.includes(siteHost()); } catch (_) { /* Menu remains usable while offline. */ }
            if (version !== menuVersion) return;
            menuIds.push(GM_registerMenuCommand(blocked ? '✅ 解除当前网站黑名单' : '🚫 拉黑当前网站', toggleBlockedSite));
        }
    };
    registerMenus();

    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    const routeChanged = () => {
        if (state.routeUrl === location.href) return;
        state.routeUrl = location.href;
        if (state.timer) window.clearInterval(state.timer);
        state.session = null;
        removeToast();
        window.setTimeout(scan, 500);
    };
    history.pushState = function (...args) { const result = originalPushState.apply(this, args); routeChanged(); return result; };
    history.replaceState = function (...args) { const result = originalReplaceState.apply(this, args); routeChanged(); return result; };
    window.addEventListener('popstate', routeChanged);
    window.addEventListener('beforeunload', () => sync(state.session));
    state.observer = new MutationObserver(() => scan());
    state.observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
    document.addEventListener('loadedmetadata', scan, true);
    window.setTimeout(scan, 800);
})();
