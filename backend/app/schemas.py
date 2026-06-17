import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---- auth / user ----
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None
    locale: str = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    name: str | None
    locale: str
    calendar_pref: str
    timezone: str


class UserSettingsIn(BaseModel):
    name: str | None = None
    locale: str | None = None        # en | fa
    calendar_pref: str | None = None  # gregorian | jalali
    timezone: str | None = None


# ---- lists ----
class ListIn(BaseModel):
    name: str
    color: str | None = None
    icon: str | None = None
    position: int = 0


class ListOut(ListIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    archived: bool


# ---- tasks ----
class TaskIn(BaseModel):
    title: str
    notes: str | None = None
    list_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    status: str = "todo"
    priority: int = 0
    due_at: datetime | None = None
    remind_at: datetime | None = None
    recurrence_rrule: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    list_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    status: str | None = None
    priority: int | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    recurrence_rrule: str | None = None
    position: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    notes: str | None
    list_id: uuid.UUID | None
    project_id: uuid.UUID | None
    parent_task_id: uuid.UUID | None
    status: str
    priority: int
    due_at: datetime | None
    remind_at: datetime | None
    recurrence_rrule: str | None
    position: int
    completed_at: datetime | None
    source: str


# ---- projects ----
class ProjectIn(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    status: str = "active"
    start_date: date | None = None
    due_date: date | None = None
    position: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    status: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    position: int | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    color: str | None
    status: str
    start_date: date | None
    due_date: date | None
    position: int


# ---- habits ----
class HabitIn(BaseModel):
    name: str
    color: str | None = None
    schedule: str = "daily"
    target_per_period: int = 1
    unit: str | None = None


class HabitUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    schedule: str | None = None
    target_per_period: int | None = None
    unit: str | None = None
    archived: bool | None = None


class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    color: str | None
    schedule: str
    target_per_period: int
    unit: str | None
    archived: bool
    today_completed: bool = False
    streak: int = 0


class HabitLogIn(BaseModel):
    log_date: date | None = None   # defaults to today
    value: int = 1


class HabitStatsOut(BaseModel):
    streak: int
    total_logs: int
    completion_rate_30d: float


# ---- pomodoro ----
class PomodoroSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    work_min: int
    short_break: int
    long_break: int
    cycles_before_long: int
    auto_start: bool


class PomodoroSettingsIn(BaseModel):
    work_min: int | None = None
    short_break: int | None = None
    long_break: int | None = None
    cycles_before_long: int | None = None
    auto_start: bool | None = None


class PomodoroSessionIn(BaseModel):
    task_id: uuid.UUID | None = None
    type: str = "work"          # work | break
    started_at: datetime
    ended_at: datetime
    completed: bool = True


class PomodoroSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID | None
    type: str
    started_at: datetime
    ended_at: datetime | None
    completed: bool


class PomodoroStatsOut(BaseModel):
    today_work_minutes: int
    week_work_minutes: int
    today_sessions: int


# ---- AI ----
class AiMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str | None
    resulting_task_ids: list | None
    created_at: datetime


class AiConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str | None
    created_at: datetime


class AiConversationDetailOut(AiConversationOut):
    messages: list[AiMessageOut] = []


class AiChatIn(BaseModel):
    text: str
    conversation_id: uuid.UUID | None = None


class AiChatOut(BaseModel):
    reply: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    created_tasks: list[TaskOut]


# ---- files ----
class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    mime: str | None
    size: int | None
    web_view_link: str | None
    attached_type: str | None
    attached_id: uuid.UUID | None
    created_at: datetime
