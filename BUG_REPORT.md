# Swan — Bug Report: recurring tasks ignore their RRULE

## Summary
Completing a recurring task **always** schedules the next instance for
"tomorrow" (`now + 1 day`), regardless of the task's recurrence rule. A weekly
task becomes daily, a monthly task becomes daily, "every Monday" becomes daily,
and so on. The recurrence engine is effectively dead code.

## Location
`backend/app/services/recurrence.py` → `next_occurrence()`

## Root cause
```python
rule = rrulestr(rrule_str, dtstart=after, ignoretz=True)
nxt  = rule.after(after.replace(tzinfo=None))
```
- `dtstart=after` is a **timezone-aware** datetime (task due dates are stored
  tz-aware UTC). `ignoretz=True` only affects timezones embedded in the rule
  *string* — it does **not** strip the tzinfo from the `dtstart` object. So the
  rrule produces tz-aware occurrences.
- `rule.after(after.replace(tzinfo=None))` then passes a **naive** search point.
- dateutil compares the naive search point against tz-aware occurrences →
  `TypeError: can't compare offset-naive and offset-aware datetimes`.
- That `TypeError` is swallowed by the bare `except Exception: return None`, so
  `next_occurrence()` returns `None` for every normal task.
- `compute_next_task_dates()` sees `None` and hits its fallback:
  `new_due = now + timedelta(days=1)`.

The broad `except` is what hid this: the function never visibly errored, it just
silently always returned the wrong answer.

## Reproduction (no DB needed)
```
FREQ=WEEKLY , due tomorrow -> next due gap from old due = 0 days   (expected ~7)
FREQ=MONTHLY, due tomorrow -> next due gap from old due = 0 days   (expected ~30)
FREQ=DAILY  , due tomorrow -> next due == old due (delta 0s)       (expected +1 day)
next_occurrence("FREQ=WEEKLY", <tz-aware now>) -> None             (expected a date)
```

## Fix
Do all rrule math in naive space consistently, then re-stamp UTC:
```python
anchor = after.replace(tzinfo=None)
rule   = rrulestr(rrule_str, dtstart=anchor)
nxt    = rule.after(anchor)
return nxt.replace(tzinfo=timezone.utc) if nxt else None
```

After the fix: WEEKLY advances ~7 days, MONTHLY ~30 days, DAILY +1 day, the
remind_at offset is preserved, and an invalid RRULE still falls back gracefully.

## Files
- `recurrence.py` — drop-in replacement for `backend/app/services/recurrence.py`
- `test_recurrence.py` — regression tests for `backend/tests/`
  (6 tests: 4 fail on the old code, all 6 pass on the fix).

## Follow-up (not fixed here, flagged)
1. The bare `except Exception` masked this bug for the life of the file. Consider
   narrowing it or logging the swallowed exception.
2. Completing an *overdue* recurring task still advances from the old due date,
   so the next instance can also be in the past. If you want "next future
   occurrence", search from `max(old_due_at, now)`.
