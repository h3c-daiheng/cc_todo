# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend
cd backend && pip install -r requirements.txt       # Install dependencies
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload  # Run dev server
cd backend && python3 -m pytest tests/ -v           # Run all tests
cd backend && python3 -m pytest tests/test_tasks.py -v  # Run single test file
cp backend/admin.yaml.example backend/admin.yaml   # Edit admin credentials, then start the app

# Frontend
cd frontend && npm install                          # Install dependencies
cd frontend && npm run dev                          # Dev server (port 5173, proxies /api to :8000)
cd frontend && npm run build                        # Production build
```

## Architecture

**Backend:** FastAPI + SQLAlchemy + SQLite (WAL mode) at `/backend/`
**Frontend:** Vue 3 + Element Plus + Pinia + Vue Router at `/frontend/`

Frontend Vite dev server proxies `/api` requests to backend port 8000. All API routes are mounted under `/api/v1`.

### Backend Structure

- `main.py` — App entry, mounts all routers, starts APScheduler on startup
- `config.py` — Env-based config (`TODO_SECRET_KEY`, `TODO_UPLOAD_DIR`)
- `database.py` — SQLAlchemy engine/session with SQLite WAL + foreign keys
- `dependencies.py` — Shared FastAPI deps: `get_current_user`, `require_admin`, permission enforcement (`ensure_task_view_permission`, `ensure_task_edit_permission`, etc.), brute-force IP tracking
- `scheduler.py` — APScheduler daily email reminder job
- `routers/` — auth, tasks, teams, comments, attachments, users (admin), settings (admin)
- `services/auth.py` — bcrypt hashing, JWT encode/decode
- `services/email.py` — Fernet SMTP password encryption, send_email via smtplib

### Frontend Structure

- `src/api/index.js` — Axios instance with 401 auto-refresh interceptor. Tokens in memory only (not localStorage)
- `src/stores/user.js` — Pinia store for auth state
- `src/router/index.js` — Route guards check `meta.public` and `meta.requireAdmin`
- `src/views/` — Pages: Login, MyTasks (kanban), TaskDetail, TeamTasks, TeamManage, admin/UserManage, admin/SystemSettings
- `src/components/` — TaskBoard (vuedraggable kanban), TaskCard, CommentList, FileUpload

## Key Conventions

**API response format** — All endpoints return `{"code": 0, "message": "ok", "data": ...}` via `ok(data)` helper in each router.

**Auth flow** — Login returns access_token (8h JWT, Bearer header) + refresh_token (7d HttpOnly cookie). Axios interceptor auto-refreshes on 401.

**Permission model:**
- Admin (`is_admin=True`): full access
- Task creator: edit/delete task
- Task assignee: update status only
- Team leader (`team.created_by`): manage members, edit team tasks
- Team member: view team tasks, comment, upload
- Enforcement via dependency functions in `dependencies.py`

**Task states:** `pending` | `in_progress` | `done`
**Task priorities:** `low` | `medium` | `high`

## Testing

Tests use in-memory SQLite with per-test schema creation. Key fixtures in `tests/conftest.py`:
- `client` — TestClient with overridden `get_db`
- `admin_user` / `normal_user` — Pre-created users
- `auth_headers` / `admin_headers` — JWT Bearer headers

Pattern: create user via fixture → get auth headers → call API → assert response.

## Important Details

- SQLite WAL mode enabled for concurrent APScheduler + HTTP access
- SMTP passwords encrypted with Fernet (key derived from `SECRET_KEY[:32]`)
- File uploads: MIME verified via `python-magic`, stored with UUID filename in `UPLOAD_DIR`
- Brute-force: 10 failed logins in 5 min → 15 min IP lockout (in-memory, resets on restart)
- Scheduler job ID `"daily_email"`, dynamically rescheduled when `email_send_hour` setting changes
- Admin accounts: defined in `backend/admin.yaml` (gitignored), auto-created on startup if user doesn't exist. Copy from `admin.yaml.example`.
