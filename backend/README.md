# CrossVideo backend

FastAPI service for authentication and cross-device video progress sync.

## Requirements

- Python 3.11 or newer (3.12 recommended)
- PostgreSQL 16 or newer

## Local setup

```bash
# 兼容模式
cd backend
uv python install 3.12    # optional
uv python pin 3.12
uv venv --python 3.12    # create venv
uv pip install -r requirements.txt
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --log-config logging.ini

# 项目模式
cd backend
uv init
uv python pin 3.12
uv add -r requirements.txt
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --log-config logging.ini
```

Uvicorn 使用 `logging.ini` 输出带时间戳的应用和访问日志。

The API is available at `http://localhost:8000`, with OpenAPI docs at `/docs`.

The userscript asks for the API base address in its login/register window. Enter only the server address, for example `http://127.0.0.1:8000`; the `/api/v1` path is added automatically. The address is stored in Tampermonkey global storage.

## Tests

```bash
cd backend
uv run pytest tests -q
```

The production database is PostgreSQL. Alembic manages all schema changes. The Compose volume `postgres-data` persists database data independently from the API container.

Access tokens are valid for 30 days by default and are renewed on each authenticated API response. Clients should save the `X-Access-Token` response header; the web admin and both userscripts do this automatically. Configure `CROSSVIDEO_ACCESS_TOKEN_EXPIRE_MINUTES` to override the lifetime.

Account security adds a server-verified click-order CAPTCHA to login and registration, TOTP two-factor authentication, email verification, and password reset. Configure `CROSSVIDEO_SMTP_HOST`, `CROSSVIDEO_SMTP_PORT`, `CROSSVIDEO_SMTP_USERNAME`, `CROSSVIDEO_SMTP_PASSWORD`, `CROSSVIDEO_SMTP_FROM_EMAIL`, and `CROSSVIDEO_SMTP_STARTTLS` to enable email delivery. Set `CROSSVIDEO_FRONTEND_BASE_URL` to the public frontend base ending in `/admin`, so verification links return to the correct app. The self-hosted CAPTCHA is a basic bot deterrent, not a robust replacement for a commercial risk-based CAPTCHA.

Email verification and password-reset sends are limited to one message per account and purpose every 60 seconds, with a maximum of five per hour.

## Superuser administration

Run these commands from `backend/` after configuring the database and applying migrations. Password input and confirmation are hidden:

```bash
uv run alembic upgrade head
uv run python -m app.commands create-superuser admin
uv run python -m app.commands set-password admin
uv run python -m app.commands list-superusers
```

The commands use Python's built-in `argparse` and `getpass`, so no extra CLI framework is required. `create-superuser` creates an account directly, without public registration or CAPTCHA. Superusers see the **用户管理** page, where they can view regular users and superusers separately and disable or re-enable regular accounts. These privileges are checked by the API as well as the frontend. A disabled account cannot sign in or use authenticated HTTP or WebSocket endpoints.

The film/TV discussion assistant uses the DeepSeek chat-completions API. Configure `CROSSVIDEO_DEEPSEEK_API_KEY`, and optionally `CROSSVIDEO_DEEPSEEK_BASE_URL` and `CROSSVIDEO_DEEPSEEK_MODEL`. `CROSSVIDEO_MONTHLY_AI_TOKEN_QUOTA` defaults to 1,000 tokens per account per UTC calendar month. The service streams assistant text as server-sent events, renders sanitized Markdown in the browser, reserves quota while requests are in flight, persists a single conversation per user, and runs an additional topic-classification request before generating a response. The streaming browser request sends the access token in the `Authorization` header.

## Docker

```bash
cd backend
docker compose up --build
```

Compose starts PostgreSQL with a persistent `postgres-data` volume and runs `alembic upgrade head` before starting the API. Set `POSTGRES_PASSWORD`, `CROSSVIDEO_SECRET_KEY`, and `CADDY_SITE_ADDRESS` in `.env` before starting.

Caddy is the only public application entry point. It proxies `/api/*` to FastAPI and serves static files from `backend/admin/`. Ports `8000` and `5432` are not published to the host.

For a server IP, Caddy can attempt automatic HTTPS when ports 80 and 443 are publicly reachable. Public CA support for IP certificates varies; a real domain name is the most portable option. If Caddy falls back to its internal CA, browsers will require trusting that CA manually.

Authenticated users can block a website from the userscript menu. Blocking removes that user's existing records for the exact hostname and causes future sync requests from that hostname to be ignored.

## Playback coordination and admin DevTools guard

The playback WebSocket is `/api/v1/ws/playback`; this deployment runs one Uvicorn worker, so live device state is held in that process and connections without heartbeats are closed after five minutes. If the API is scaled to multiple workers or replicas, shared Redis Pub/Sub/state is needed so pause commands reach every worker.

The production admin UI uses `devtools-detect` to obscure the dashboard while DevTools appears open. Vite development mode disables the guard automatically. To disable it in another build, set `VITE_DISABLE_DEVTOOLS_GUARD=true`. Detection is only a deterrent, not a security boundary; the upstream library notes possible false positives.

Successful progress syncs update each user's `user_sites` record and the ten most recently watched sites are offered as filters across history, favorites, and watch-later. Dashboard watch time is an estimate based on progress advances; it is not a browser-level time tracker. Bulk delete endpoints accept 1–50 IDs and only delete records owned by the authenticated user. The admin blocklist accepts a hostname or URL and removes matching history records when a site is added.

Episode titles recognized by `guessit` are normalized into per-user, per-title, per-season, per-episode progress. The original URL-specific history remains available and links to this episode record. Resume queries accept the page title and return `cross_site: true` when progress comes from another URL; the userscript uses that flag to show a cross-site resume prompt. The dashboard's **影视进度** page lists recognized episodes by most recently updated. The bounded in-process title cache avoids repeated parsing without requiring Redis.

On the first progress sync for a site, the API schedules a bounded homepage-title check in a FastAPI background task. The result is stored as the site's display name when available, and `title_fetch_attempted` prevents subsequent syncs from repeating the check. Requests are limited to public IP addresses, use short timeouts, and do not follow redirects. This in-process task is best-effort; deployments that need durable retries should move it to a persistent task queue.
