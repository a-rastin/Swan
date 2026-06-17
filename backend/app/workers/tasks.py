"""Celery tasks."""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import celery


# ── helpers ──────────────────────────────────────────────────────────────────

async def _dispatch_due_reminders_async() -> int:
    from app.db.session import SessionLocal
    from app.models import PushSubscription, Task, TelegramLink
    from app.services.push import send_push
    from app.services.telegram_out import notify_n8n

    now = datetime.now(timezone.utc)
    sent = 0

    async with SessionLocal() as db:
        tasks = await db.scalars(
            select(Task).where(
                Task.remind_at <= now,
                Task.status != "done",
            )
        )
        tasks = list(tasks)

        for task in tasks:
            # web push
            subs = await db.scalars(
                select(PushSubscription).where(PushSubscription.user_id == task.user_id)
            )
            for sub in subs:
                send_push(
                    {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                    title="Swan reminder",
                    body=task.title,
                    url=f"/tasks/{task.id}",
                )

            # telegram via n8n (if linked)
            tg = await db.scalar(
                select(TelegramLink).where(
                    TelegramLink.user_id == task.user_id,
                    TelegramLink.telegram_chat_id.isnot(None),
                )
            )
            if tg and tg.telegram_chat_id:
                await notify_n8n(
                    tg.telegram_chat_id,
                    f"⏰ Reminder: {task.title}",
                    {"task_id": str(task.id)},
                )

            # clear remind_at so it doesn't re-fire
            task.remind_at = None
            sent += 1

        if tasks:
            await db.commit()

    return sent


async def _spawn_recurring_async() -> None:
    """Midnight job: spawn next instance for tasks whose recurrence_rrule fired but no
    next instance exists yet. Distinct from complete_task path (handles tasks that were
    completed via external sources without hitting the API)."""
    # Phase 2: habits reset also goes here.
    pass


# ── celery tasks ──────────────────────────────────────────────────────────────

@celery.task
def dispatch_due_reminders():
    return asyncio.run(_dispatch_due_reminders_async())


@celery.task
def spawn_recurring_and_reset_habits():
    asyncio.run(_spawn_recurring_async())


@celery.task
def send_daily_digest(user_id: str):
    # Phase 3: build today's tasks+habits digest, push + n8n/telegram.
    pass
