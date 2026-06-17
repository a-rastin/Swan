import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import AiConversation, AiMessage, Task, User
from app.schemas import (
    AiChatIn,
    AiChatOut,
    AiConversationDetailOut,
    AiConversationOut,
    AiMessageOut,
    TaskOut,
)
from app.services.gemini import analyze_audio, analyze_text

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_or_create_conv(
    db: AsyncSession, user: User, conv_id: uuid.UUID | None
) -> AiConversation:
    if conv_id:
        conv = await db.get(AiConversation, conv_id)
        if conv is None or conv.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found")
        return conv
    # use latest or create new
    latest = await db.scalar(
        select(AiConversation)
        .where(AiConversation.user_id == user.id)
        .order_by(AiConversation.created_at.desc())
        .limit(1)
    )
    if latest:
        return latest
    conv = AiConversation(user_id=user.id)
    db.add(conv)
    await db.flush()
    return conv


async def _load_history(db: AsyncSession, conv_id: uuid.UUID) -> list[dict]:
    msgs = list(await db.scalars(
        select(AiMessage)
        .where(AiMessage.conversation_id == conv_id)
        .order_by(AiMessage.created_at)
    ))
    return [{"role": m.role, "content": m.content or ""} for m in msgs]


def _parse_due(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


async def _create_tasks(db: AsyncSession, user: User, raw_tasks: list[dict]) -> list[Task]:
    created: list[Task] = []
    for t in raw_tasks:
        if not isinstance(t, dict) or not t.get("title"):
            continue
        obj = Task(
            user_id=user.id,
            title=str(t["title"])[:255],
            notes=str(t["notes"])[:2000] if t.get("notes") else None,
            priority=int(t.get("priority", 0)) if str(t.get("priority", 0)).isdigit() else 0,
            due_at=_parse_due(t.get("due_at")),
            source="ai",
        )
        db.add(obj)
        created.append(obj)
    if created:
        await db.flush()
    return created


async def _finish(
    db: AsyncSession,
    user: User,
    conv: AiConversation,
    user_text: str | None,
    result: dict,
    audio_ref: str | None = None,
) -> AiChatOut:
    tasks = await _create_tasks(db, user, result.get("tasks") or [])
    reply = result.get("reply") or ""

    user_msg = AiMessage(
        conversation_id=conv.id,
        role="user",
        content=user_text,
        audio_ref=audio_ref,
    )
    asst_msg = AiMessage(
        conversation_id=conv.id,
        role="assistant",
        content=reply,
        resulting_task_ids=[str(t.id) for t in tasks] if tasks else None,
    )
    db.add(user_msg)
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    return AiChatOut(
        reply=reply,
        conversation_id=conv.id,
        message_id=asst_msg.id,
        created_tasks=[TaskOut.model_validate(t) for t in tasks],
    )


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=list[AiConversationOut])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    rows = list(await db.scalars(
        select(AiConversation)
        .where(AiConversation.user_id == user.id)
        .order_by(AiConversation.created_at.desc())
        .limit(50)
    ))
    return rows


@router.post("/conversations", response_model=AiConversationOut, status_code=201)
async def new_conversation(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    conv = AiConversation(user_id=user.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conv_id}", response_model=AiConversationDetailOut)
async def get_conversation(
    conv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    conv = await db.get(AiConversation, conv_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found")
    msgs = list(await db.scalars(
        select(AiMessage)
        .where(AiMessage.conversation_id == conv_id)
        .order_by(AiMessage.created_at)
    ))
    out = AiConversationDetailOut.model_validate(conv)
    out.messages = [AiMessageOut.model_validate(m) for m in msgs]  # type: ignore[attr-defined]
    return out


@router.post("/chat", response_model=AiChatOut)
async def chat(
    body: AiChatIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    conv = await _get_or_create_conv(db, user, body.conversation_id)
    history = await _load_history(db, conv.id)
    result = analyze_text(body.text, history)
    return await _finish(db, user, conv, user_text=body.text, result=result)


@router.post("/voice", response_model=AiChatOut)
async def voice(
    audio: UploadFile = File(...),
    conversation_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
    conv = await _get_or_create_conv(db, user, conv_uuid)
    history = await _load_history(db, conv.id)

    data = await audio.read(20 * 1024 * 1024)  # 20 MB cap
    mime = audio.content_type or "audio/webm"
    result = analyze_audio(data, mime=mime, history=history)

    return await _finish(
        db, user, conv,
        user_text=None,
        result=result,
        audio_ref=audio.filename,
    )
