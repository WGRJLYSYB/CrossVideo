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
uv run uvicorn app.main:app --reload --log-config logging.ini

# 项目模式
cd backend
uv init
uv python pin 3.12
uv add -r requirements.txt
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

The production database is PostgreSQL. The Compose volume `postgres-data` persists database data independently from the API container.

## Docker

```bash
cd backend
docker compose up --build
```

Compose starts PostgreSQL with a persistent `postgres-data` volume. Set `POSTGRES_PASSWORD` and `CROSSVIDEO_SECRET_KEY` in `.env` before starting. The previous SQLite database is not migrated automatically; export/import it separately if existing history must be retained.

Authenticated users can block a website from the userscript menu. Blocking removes that user's existing records for the exact hostname and causes future sync requests from that hostname to be ignored.
