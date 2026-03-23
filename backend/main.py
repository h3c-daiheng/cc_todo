# backend/main.py
from fastapi import FastAPI
from database import create_tables
from routers import auth, tasks, teams, comments, attachments, users, settings

app = FastAPI(title="Todo App API")

@app.on_event("startup")
def startup():
    create_tables()

    from database import SessionLocal
    from services.admin_init import ensure_admins

    db = SessionLocal()
    try:
        ensure_admins(db)

        from models import SystemSetting
        row = db.get(SystemSetting, "email_send_hour")
        hour = int(row.value) if row and row.value else 8
    finally:
        db.close()

    from scheduler import start_scheduler
    start_scheduler(hour)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(attachments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
