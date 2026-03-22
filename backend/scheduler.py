# backend/scheduler.py
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def send_daily_reminders():
    """Query overdue/due-today tasks, aggregate by assignee and team leader, send emails."""
    from database import SessionLocal
    from models import Task, User, Team
    from services.email import get_smtp_config, send_email

    db = SessionLocal()
    try:
        config = get_smtp_config(db)
        if not config:
            logger.info("SMTP not configured, skipping daily reminder emails")
            return

        today = date.today()

        # Query tasks that are due today or overdue and not done
        tasks = (
            db.query(Task)
            .filter(Task.due_date <= today, Task.status != "done")
            .all()
        )

        if not tasks:
            logger.info("No overdue/due-today tasks found, skipping emails")
            return

        # Aggregate tasks by recipient (assignee or team leader)
        recipient_tasks: dict[int, list[Task]] = {}

        for task in tasks:
            recipients = set()

            # Assignee
            if task.assigned_to:
                recipients.add(task.assigned_to)

            # Team leader
            if task.team_id:
                team = db.get(Team, task.team_id)
                if team and team.created_by:
                    recipients.add(team.created_by)

            for uid in recipients:
                recipient_tasks.setdefault(uid, []).append(task)

        # Send emails
        for user_id, user_tasks in recipient_tasks.items():
            user = db.get(User, user_id)
            if not user or not user.email or not user.email_notify or not user.is_active:
                continue

            overdue = [t for t in user_tasks if t.due_date < today]
            due_today = [t for t in user_tasks if t.due_date == today]

            rows = ""
            for t in user_tasks:
                status_label = "逾期" if t.due_date < today else "今日到期"
                rows += (
                    f"<tr>"
                    f"<td>{t.id}</td>"
                    f"<td>{t.title}</td>"
                    f"<td>{t.due_date}</td>"
                    f"<td>{t.status}</td>"
                    f"<td>{status_label}</td>"
                    f"</tr>"
                )

            body = f"""
<html><body>
<p>您好 {user.username}，</p>
<p>以下任务需要您关注（逾期 {len(overdue)} 项，今日到期 {len(due_today)} 项）：</p>
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr><th>ID</th><th>标题</th><th>截止日期</th><th>状态</th><th>备注</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<p>请及时处理，谢谢。</p>
</body></html>
"""
            try:
                send_email(
                    to=user.email,
                    subject=f"任务提醒：您有 {len(user_tasks)} 项任务需要处理",
                    body=body,
                    config=config,
                )
            except Exception as exc:
                logger.error(f"发送邮件至 {user.email} 失败: {exc}")

    except Exception as exc:
        logger.error(f"send_daily_reminders 异常: {exc}")
    finally:
        db.close()


def reschedule_email_job(hour: int):
    """Reschedule the daily_email job to a new hour."""
    if _scheduler.get_job("daily_email"):
        _scheduler.reschedule_job(
            "daily_email",
            trigger=CronTrigger(hour=hour, minute=0),
        )
        logger.info(f"daily_email job rescheduled to hour={hour}")
    else:
        logger.warning("daily_email job not found, cannot reschedule")


def start_scheduler(hour: int = 8):
    """Add the daily_email cron job and start the scheduler."""
    _scheduler.add_job(
        send_daily_reminders,
        trigger=CronTrigger(hour=hour, minute=0),
        id="daily_email",
        replace_existing=True,
    )
    if not _scheduler.running:
        _scheduler.start()
    logger.info(f"Scheduler started, daily_email job at hour={hour}")
