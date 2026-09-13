# 全平台视频观看进度同步工具（Userscript + FastAPI）需求开发文档 (PRD)

---

## 1. 项目概述

### 1.1 背景与痛点

用户经常在多个设备（如 Windows、macOS）以及多个视频平台（如 YouTube、Bilibili、腾讯视频、爱奇艺及第三方网页播放器）观看长视频。由于缺乏跨平台/跨设备的统一进度追踪机制，用户在换设备或重新打开网页时无法接续上次的播放节点。

### 1.2 项目目标

开发一套轻量级的**跨平台视频观看进度同步系统**：

* **前端：** 基于油猴脚本（Tampermonkey / Violentmonkey Userscript）实现全网 `<video>` 播放器的通用监听、智能识别与原生 UI 交互。
* **后端：** 基于 FastAPI + SQLite 提供极轻量级的用户鉴权、高效 URL 哈希索引与进度数据同步接口。

---

## 2. 总体架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    油猴脚本前端 (Userscript)                     │
│                                                                 │
│  [DOM 视频过滤器] ──► [防抖采集/恢复逻辑] ──► [登录/注册/历史 UI] │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ Authorization: Bearer <JWT>
                                  │ GM_xmlhttpRequest (REST API)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI 后端服务                           │
│                                                                 │
│   [Auth 认证模块]      [API 路由 / SHA256 索引]   [路由&防抖处理]│
└─────────────────────────────────┬───────────────────────────────┘
                                  │ ORM / Direct SQL
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite 数据库 (WAL 模式)                    │
└─────────────────────────────────────────────────────────────────┘

```

---

## 3. 前端（油猴脚本）功能规范

### 3.1 全局存储与状态管理

* **存储机制：** 必须使用油猴原生 API `GM_setValue` 与 `GM_getValue` 存储登录产生的 JWT Token。
* **域间共享：** 账号登录状态在所有网站全局生效，换域名无需重复登录。

### 3.2 界面交互（UI/UX 规范）

通过油猴原生菜单 `GM_registerMenuCommand` 提供两个核心入口：

#### 1. 登录/注册 Modal 弹窗

* **触发方式：** 点击油猴菜单中的 `[🔑 登录 / 注册账号]`。已登录状态下显示为 `[👤 已登录：username (点击退出)]`。
* **界面组成：** 在网页中央弹出半透明遮罩卡片，包含 Tab 选项卡（登录 / 注册）：
* **登录模式：** 输入框（用户名、密码）。
* **注册模式：** 输入框（用户名、密码、确认密码），支持免验证码快速注册。


* **校验逻辑：** 校验两次密码输入一致性、密码复杂度（≥ 8 位且包含字母+数字）、用户名是否重复。

#### 2. 历史记录 Drawer 抽屉/ Modal

* **触发方式：** 点击油猴菜单中的 `[📜 查看播放历史]`。
* **展示形式：** 分页展示当前用户的播放历史，每页 **10 条** 记录，按 `updated_at DESC` 倒序排列。
* **显示内容：** 网页标签页标题 (`document.title`)、净化后的 URL、当前进度/总时长（格式为 `HH:MM:SS`）、播放进度百分比、更新时间。
* **交互：** 点击记录条目即可直接跳转至 `clean_url` 对应的视频页面。

### 3.3 智能视频过滤算法（排除广告与背景视频）

脚本加载后动态扫描页面中的 `<video>` 元素，只有**同时满足**以下条件的视频才会被判定为目标视频：

1. **尺寸占比：** 视频渲染宽度占当前视口（Viewport）宽度比例大于 50%（`videoWidth / window.innerWidth > 0.5`），或视频处于全屏/网页全屏模式。
2. **总时长：** 视频总时长 `video.duration` 必须大于 **180 秒（3 分钟）**。
3. **用户行为验证：** 视频必须被用户主动播放超过 **10 秒**，或触发过用户手动交互（点击播放/取消静音），防止后台静眠加载广告触发记录。

### 3.4 交互与进度恢复逻辑

1. **进场检测：** 识别到有效视频后，前端净化得到 `clean_url` 并计算 `url_hash = SHA256(clean_url)`，带 Token 请求后端接口 `GET /api/v1/progress/query?url_hash=xxx`。
2. **Toast 恢复提示：**
* 若查询到历史进度（例如 `00:42:15`），在播放器右上角悬浮展示存留 **6 秒** 的轻量 Toast 提示框：
`💡 检测到您上次观看至 42:15 [跳转恢复] [从头观看]`
* **点击 [跳转恢复]：** 执行 `video.currentTime = 2535` 并继续播放。
* **点击 [从头观看] 或 忽略提示：** 从 0 秒重新计时并覆盖更新。


3. **防抖上传策略：**
* **定时上传：** 视频正常播放时，采用 **15 秒间隔** 的定时器向后端同步最新播放秒数。
* **关键事件触发：** 监听视频 `pause`（暂停）事件及页面 `beforeunload`（关闭/刷新）事件，实时触发同步。



---

## 4. 后端（FastAPI）与数据库规范

### 4.1 数据库结构设计 (SQLite)

数据库须启用 **WAL (Write-Ahead Logging)** 模式以增强并发写入能力。

#### 1. 用户表 `users`

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 记录创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 记录更新时间（如修改密码）
);

```

#### 2. 播放进度表 `playback_progress`

```sql
CREATE TABLE playback_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    url_hash VARCHAR(64) NOT NULL,    -- SHA256(clean_url)，用于精准高效索引
    clean_url TEXT NOT NULL,           -- 规范化后的完整 URL，用于前端跳转展示
    title TEXT NOT NULL,               -- 网页标题 (document.title)
    progress_seconds REAL NOT NULL,    -- 播放进度（秒）
    duration REAL NOT NULL,            -- 视频总时长（秒）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 首次观看/记录时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 最近一次观看进度更新时间
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_user_url ON playback_progress(user_id, url_hash);

```

### 4.2 URL 规范化清洗算法 (URL Sanitization Engine)

在前端生成 `url_hash` 及 `clean_url` 之前，必须执行以下净化规则：

1. **保留核心视频 ID 参数：**
* Bilibili: 保留 `p`（分 P 参数）与 `t` 参数。
* YouTube: 保留 `v` 参数。


2. **剥离追踪与垃圾参数：**
* 剔除所有以 `utm_`、`spm_`、`from`、`ref`、`source`、`vd_source` 开头的 Query 参数。


3. **哈希计算：** 使用 JavaScript 原生 `crypto.subtle.digest('SHA-256', ...)` 生成 64 位十六进制字符串 `url_hash`。

---

## 5. API 接口规范

所有的 API 请求除认证接口外，必须在 Header 中附加 `Authorization: Bearer <JWT_TOKEN>`。

### 5.1 认证模块

#### 1. 用户注册

* **接口：** `POST /api/v1/auth/register`
* **Request Body:**
```json
{
  "username": "user123",
  "password": "Password123",
  "confirm_password": "Password123"
}

```


* **Response (200 OK):**
```json
{
  "message": "User registered successfully"
}

```



#### 2. 用户登录

* **接口：** `POST /api/v1/auth/login`
* **Request Body:** Standard OAuth2 Form Data (`username`, `password`)
* **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}

```



---

### 5.2 进度与数据同步模块

#### 1. 防抖同步 / 更新进度

* **接口：** `POST /api/v1/progress/sync`
* **Request Body:**
```json
{
  "url_hash": "a3f89b...",
  "clean_url": "https://www.bilibili.com/video/BV1xx411c7mD?p=1",
  "title": "【高清】某某经典电影_哔哩哔哩_bilibili",
  "progress_seconds": 1254.5,
  "duration": 5400.0
}

```


* **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Progress updated"
}

```



#### 2. 查询单个视频历史进度 (依据哈希匹配)

* **接口：** `GET /api/v1/progress/query`
* **Query Params:** `url_hash=a3f89b...`
* **Response (200 OK - 存在记录):**
```json
{
  "found": true,
  "progress_seconds": 1254.5,
  "duration": 5400.0,
  "updated_at": "2026-06-15 14:30:00"
}

```


* **Response (200 OK - 无记录):**
```json
{
  "found": false
}

```



#### 3. 分页获取用户历史列表

* **接口：** `GET /api/v1/progress/list`
* **Query Params:** `page=1` (默认 1), `page_size=10` (默认 10)
* **Response (200 OK):**
```json
{
  "total": 45,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": 102,
      "clean_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
      "progress_seconds": 120.0,
      "duration": 213.0,
      "updated_at": "2026-06-15 12:00:00"
    }
  ]
}

```



---

## 6. 项目交付物清单

1. **FastAPI 服务端源码项目：**
* 包含数据库表结构自动初始化建表逻辑（SQLAlchemy / SQLModel / 原生 asyncpg/aiosqlite）。
* 提供 Docker 部署所需的 `Dockerfile` 与 `docker-compose.yml`。


2. **油猴脚本源码 (`.user.js`)：**
* 包含完整的油猴 Header 声明（配置 `@grant GM_setValue`, `@grant GM_getValue`, `@grant GM_xmlhttpRequest`, `@grant GM_registerMenuCommand`）。
* 内置登录/注册 UI、历史列表 Modal/Drawer UI、Toast 提示 UI 及 CSS 样式注入。


---

## 7. 核心补充与边缘场景处理规范 (Edge Cases & Advanced Features)

### 7.1 动态单页应用（SPA）与无刷新换集监听

在 Bilibili、YouTube 等现代视频网站中，用户切换剧集（如从第 1 集自动切到第 2 集）或点击推荐视频时，页面不会发生刷新，仅通过 HTML5 History API 修改 URL 并更换 `<video>` 元素的 `src` 属性。

#### 客户端 (Userscript) 处理逻辑：

1. **URL 变更监听：**
* 重写 `history.pushState` 与 `history.replaceState` 方法，并监听 `popstate` 事件。
* 当 URL 发生变化时，立即销毁当前的防抖定时器（Timer），清理之前的 Toast 提示框。


2. **视频源变更监听：**
* 使用 `MutationObserver` 监听 `<video>` 节点的 `src` 属性变化，或全局监听 `<video>` 的 `loadedmetadata` 事件。


3. **重新触发初始化：** 确认视频源/URL 变化后，自动对新 URL 进行规范化清洗，并重新向后端发送 `GET /api/v1/progress/query?url_hash=xxx` 查询新视频的进度。

---

### 7.2 进度同步冲突与覆盖策略 (Conflict Resolution)

在多设备并发或多标签页打开同一视频时，可能存在本地设备进度较旧、网络延迟导致的“断点覆盖”问题。

#### 同步机制（采用 Last-Modified-Wins 结合播放进度优先）：

1. **客户端上报时（`POST /api/v1/progress/sync`）：**
* 上报数据包中附加客户端的本地更新时间戳 `client_updated_at`。


2. **服务端判定逻辑：**
* 当收到同步请求时，比对 SQLite 中已有的 `updated_at`。
* **覆盖原则：** 只有当 `client_updated_at` 晚于数据库中的 `updated_at` **或者** 新上报的 `progress_seconds` 大于数据库存量进度（非重置播放状态下）时，才执行数据库 UPDATE。防止离线/残存标签页上传旧进度覆盖最新进度。



---

### 7.3 跨域与网络请求规范 (CORS & Security)

为了保障油猴脚本在任意视频网站（如 `bilibili.com`、`youtube.com`）均能正常与自定义 FastAPI 后端通信：

1. **油猴端网络请求：**
* **必须** 声明 `// @grant GM_xmlhttpRequest`，并统一使用 `GM_xmlhttpRequest` 发起所有 REST API 请求。
* **严禁** 使用原生 `fetch` 或 `XMLHttpRequest`，避免被目标网站本身的 CORS（跨源资源共享）或 CSP（内容安全策略）直接拦截。


2. **FastAPI 服务端跨域配置：**
* 服务端必须显式引入 `CORSMiddleware`，开启全局 CORS 允许，允许自定义 Header 携带 `Authorization: Bearer <JWT>`。



---

### 7.4 结尾完成检测与数据库保养 (Cleanup & Finish Logic)

1. **视频播放完成/结尾判定（95% 阈值）：**
* 当视频播放进度达到总时长的 **95% 以上**（即 `progress_seconds / duration >= 0.95`）时，系统自动将数据库中的 `progress_seconds` 重置为 `0` 或将该记录标记为 `completed`。
* **效果：** 用户下次重新打开该视频时，不再展示“恢复上次进度”的提示框，避免反复恢复到视频尾声/片尾曲。


2. **数据库冗余数据清理：**
* 后端提供一个内部定时任务/管理接口：自动定期清理 `updated_at` 在 **1 年以上** 且播放时长小于 5% 的无效/弃剧记录，保持 SQLite 的极轻量运行。



---