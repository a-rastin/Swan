from celery import Celery

from app.core.config import settings

celery = Celery("swan", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery.conf.timezone = settings.TZ
celery.conf.beat_schedule = {
    # phase 3: dispatch due reminders every minute
    "dispatch-reminders": {
        "task": "app.workers.tasks.dispatch_due_reminders",
        "schedule": 60.0,
    },
    # phase 2/3: midnight recurrence + habit reset (run hourly, guard inside)
    "recurrence-and-habits": {
        "task": "app.workers.tasks.spawn_recurring_and_reset_habits",
        "schedule": 3600.0,
    },
}

import app.workers.tasks  # noqa: E402,F401
