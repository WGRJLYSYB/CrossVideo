# CrossVideo

跨平台视频观看进度同步工具，使用油猴脚本监听网页播放器，并通过 FastAPI 服务在不同设备和视频网站之间同步观看进度。

## 功能

- 自动识别页面中的主要 HTML5 视频播放器
- 过滤小尺寸视频、短视频和未发生用户交互的视频
- 播放进度定时同步，暂停和播放结束时同步最后进度
- 页面重新打开时提示恢复历史进度
- 用户注册、登录和 JWT 鉴权
- 播放历史分页、搜索、当前网站筛选和单条删除
- 当前网站黑名单，可跨设备生效并删除该网站已有记录
- URL 清洗和 SHA-256 索引
- 登录失败递增等待，降低暴力尝试风险
- API 地址由用户在油猴脚本中配置，脚本不绑定特定服务器

## 项目结构

```text
CrossVideo/
├── backend/       # FastAPI 服务、PostgreSQL 配置和 Docker 编排
├── tampermonkey/   # 油猴脚本
└── PRD.md          # 项目需求文档
```

## 快速开始

### 方式一：使用 Docker Compose

进入后端目录：

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，至少设置一个随机的长期密钥：

```env
CROSSVIDEO_SECRET_KEY=替换为随机密钥
```

启动服务：

```bash
docker compose up --build
```

服务默认监听：

```text
http://127.0.0.1:8000
```

PostgreSQL 数据会保存到 Docker 命名卷 `backend_postgres-data`。

### 方式二：使用 uv 本地运行

要求 Python 3.11 以上，推荐 Python 3.12 和 uv。

```bash
cd backend
uv venv --python 3.12
uv pip install --python .venv -r requirements.txt
cp .env.example .env
uv run uvicorn app.main:app --reload
```

运行测试：

```bash
uv run pytest tests -q
```

## 安装油猴脚本

1. 安装 Tampermonkey 或 Violentmonkey。
2. 打开 [tampermonkey/crossvideo.user.js](tampermonkey/crossvideo.user.js)。
3. 将文件内容复制到新建的用户脚本中并保存。
4. 打开任意视频页面，从油猴菜单进入“登录 / 注册账号”。
5. 填写后端地址，例如：

```text
http://127.0.0.1:8000
```

脚本会自动补充 `/api/v1` 路径。

## API

主要接口包括：

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/progress/sync
GET    /api/v1/progress/query
GET    /api/v1/progress/list
DELETE /api/v1/progress/records/{id}
GET    /api/v1/progress/blocked-sites
POST   /api/v1/progress/blocked-sites
DELETE /api/v1/progress/blocked-sites/{site_host}
```

登录、注册和进度接口统一使用 JSON 请求体。认证后的请求使用：

```text
Authorization: Bearer <access_token>
```

线上环境默认关闭 FastAPI 的 `/docs`、`/redoc` 和 `/openapi.json` 接口文档入口。

## 数据与迁移

Docker Compose 使用宿主机目录挂载：

```yaml
- ./data:/data
```

迁移服务器时需要保留：

- `backend/data/`
- `backend/.env`
- `CROSSVIDEO_SECRET_KEY`

密钥变化会导致原有 JWT Token 失效。环境变量、虚拟环境和本地数据库文件已加入 Git 忽略规则。

## 安全说明

- 不要提交 `.env`、数据库文件或生产密钥。
- 生产环境应使用高强度随机 `CROSSVIDEO_SECRET_KEY`。
- 建议通过反向代理启用 HTTPS。
- `CROSSVIDEO_CORS_ORIGINS` 在生产环境不建议长期使用 `[*]`，应限制为实际需要的来源。
- 油猴脚本的 API 地址由用户配置，发布脚本时不会携带项目服务器地址。

## 许可证

MIT License
