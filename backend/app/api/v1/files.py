import asyncio
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import File as FileModel, User
from app.schemas import FileOut
from app.services import drive

router = APIRouter()

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("", response_model=FileOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    attached_type: str | None = Query(None),   # task | project | list
    attached_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large (max 50 MB)")

    mime = file.content_type or "application/octet-stream"
    loop = asyncio.get_event_loop()
    meta = await loop.run_in_executor(
        None,
        lambda: drive.upload_file(str(current_user.id), file.filename or "file", data, mime),
    )

    row = FileModel(
        user_id=current_user.id,
        drive_file_id=meta["id"],
        name=file.filename or "file",
        mime=mime,
        size=len(data),
        web_view_link=meta.get("webViewLink"),
        attached_type=attached_type,
        attached_id=attached_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[FileOut])
async def list_files(
    attached_type: str | None = Query(None),
    attached_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    q = select(FileModel).where(FileModel.user_id == current_user.id)
    if attached_type:
        q = q.where(FileModel.attached_type == attached_type)
    if attached_id:
        q = q.where(FileModel.attached_id == attached_id)
    result = await db.execute(q.order_by(FileModel.created_at.desc()))
    return result.scalars().all()


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    row = await db.get(FileModel, file_id)
    if not row or row.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "file not found")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: drive.delete_file(row.drive_file_id))

    await db.delete(row)
    await db.commit()
