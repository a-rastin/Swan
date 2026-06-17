"""Parse RRULE strings and compute next occurrence after a reference datetime.

Uses python-dateutil. Supports standard RRULE syntax (FREQ=DAILY, FREQ=WEEKLY;BYDAY=MO, etc.).
"""
from datetime import datetime, timedelta, timezone

from dateutil.rrule import rrulestr


def next_occurrence(rrule_str: str, after: datetime) -> datetime | None:
    """Return next datetime after `after` per `rrule_str`. Returns None if no future occurrence."""
    try:
       anchor = after.replace(tzinfo=None)
        rule   = rrulestr(rrule_str, dtstart=anchor)
        nxt    = rule.after(anchor)
        return nxt.replace(tzinfo=timezone.utc) if nxt else None
        if nxt is None:
            return None
        return nxt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def compute_next_task_dates(
    rrule_str: str,
    old_due_at: datetime | None,
    old_remind_at: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    """Return (new_due_at, new_remind_at) for next recurring instance.

    If task has due_at, the RRULE advances it. remind_at offset is preserved
    relative to due_at if both were set.
    """
    now = datetime.now(timezone.utc)
    base = old_due_at or now

    new_due = next_occurrence(rrule_str, base)
    if new_due is None:
        # fallback: 1-day advance
        new_due = now + timedelta(days=1)

    new_remind: datetime | None = None
    if old_remind_at is not None and old_due_at is not None:
        offset = old_due_at - old_remind_at
        new_remind = new_due - offset
    elif old_remind_at is not None:
        # no due_at — shift remind by same delta as due shift
        delta = new_due - base
        new_remind = old_remind_at + delta

    return new_due, new_remind
