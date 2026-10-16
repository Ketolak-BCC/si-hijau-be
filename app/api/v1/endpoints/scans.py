from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.models.scan import ScanHistory
from app.models.user import User
from app.schemas.scan import ScanResponse
from app.services.s3_service import s3_service
from app.services.vision_service import vision_service

router = APIRouter()


@router.post("/upload-and-scan", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_scan(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File provided must be an image",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    image_url = await s3_service.upload_image(file_bytes, content_type=file.content_type)
    vision_result = await vision_service.analyze_waste_image(file_bytes, mime_type=file.content_type)

    scan = ScanHistory(
        user_id=current_user.id if current_user else None,
        image_url=image_url,
        item_name=vision_result.item_name,
        detected_category=vision_result.category.value,
        confidence_score=vision_result.confidence_score,
        raw_analysis=vision_result.raw_analysis,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


@router.get("/history", response_model=list[ScanResponse])
async def get_scan_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
    offset: int = 0,
):
    query = (
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user.id)
        .order_by(desc(ScanHistory.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
