"""Public router for participant-facing endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.participant import Participant, ParticipantStatus, MessagingChannelType
from app.models.language import AvailableLanguage

router = APIRouter()


class EnrollmentRequest(BaseModel):
    """Enrollment request schema."""
    project_code: str
    external_id: Optional[str] = None
    phone_number: Optional[str] = None
    fcm_token: Optional[str] = None
    language_code: str = "en"


class EnrollmentResponse(BaseModel):
    """Enrollment response schema."""
    participant_uuid: str
    project_name: str
    language: str
    message: str


class ParticipantStatusResponse(BaseModel):
    """Participant status response."""
    status: str
    enrolled_at: Optional[str]
    language: str


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_participant(
    data: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
) -> EnrollmentResponse:
    """Enroll a new participant in a project.

    Args:
        data: Enrollment data
        db: Database session

    Returns:
        Enrollment confirmation
    """
    from datetime import datetime, timezone

    # Find project by code
    project_result = await db.execute(
        select(Project).where(
            Project.code == data.project_code,
            Project.status == ProjectStatus.ACTIVE,
            Project.removed_at.is_(None),
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or inactive")

    # Find language
    language_result = await db.execute(
        select(AvailableLanguage).where(AvailableLanguage.code == data.language_code)
    )
    language = language_result.scalar_one_or_none()
    if not language:
        # Default to English
        language_result = await db.execute(
            select(AvailableLanguage).where(AvailableLanguage.code == "en")
        )
        language = language_result.scalar_one_or_none()
        if not language:
            raise HTTPException(status_code=500, detail="Language configuration error")

    # Check for existing enrollment by external_id
    if data.external_id:
        existing_result = await db.execute(
            select(Participant).where(
                Participant.project_id == project.id,
                Participant.external_id == data.external_id,
                Participant.removed_at.is_(None),
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Participant already enrolled")

    # Create participant
    participant = Participant(
        project_id=project.id,
        external_id=data.external_id,
        phone_number=data.phone_number,
        fcm_token=data.fcm_token,
        channel_type=MessagingChannelType.MOBILE_APP,
        current_language_id=language.id,
        status=ParticipantStatus.ACTIVE,
        enrolled_at=datetime.now(timezone.utc),
    )
    db.add(participant)
    await db.flush()
    await db.refresh(participant)

    return EnrollmentResponse(
        participant_uuid=participant.uu_id,
        project_name=project.name,
        language=language.name,
        message="Successfully enrolled",
    )


@router.get("/participant/{participant_uuid}/status", response_model=ParticipantStatusResponse)
async def get_participant_status(
    participant_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> ParticipantStatusResponse:
    """Get participant status.

    Args:
        participant_uuid: Participant UUID
        db: Database session

    Returns:
        Participant status
    """
    result = await db.execute(
        select(Participant).where(
            Participant.uu_id == participant_uuid,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Get language
    language_result = await db.execute(
        select(AvailableLanguage).where(AvailableLanguage.id == participant.current_language_id)
    )
    language = language_result.scalar_one_or_none()

    return ParticipantStatusResponse(
        status=participant.status.value,
        enrolled_at=participant.enrolled_at.isoformat() if participant.enrolled_at else None,
        language=language.name if language else "Unknown",
    )


@router.post("/participant/{participant_uuid}/fcm-token")
async def update_fcm_token(
    participant_uuid: str,
    fcm_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update participant FCM token.

    Args:
        participant_uuid: Participant UUID
        fcm_token: New FCM token
        db: Database session

    Returns:
        Success message
    """
    result = await db.execute(
        select(Participant).where(
            Participant.uu_id == participant_uuid,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    participant.fcm_token = fcm_token
    await db.flush()

    return {"message": "FCM token updated"}


@router.post("/participant/{participant_uuid}/language")
async def update_language(
    participant_uuid: str,
    language_code: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update participant language preference.

    Args:
        participant_uuid: Participant UUID
        language_code: Language code (en, es)
        db: Database session

    Returns:
        Success message
    """
    result = await db.execute(
        select(Participant).where(
            Participant.uu_id == participant_uuid,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Find language
    language_result = await db.execute(
        select(AvailableLanguage).where(AvailableLanguage.code == language_code)
    )
    language = language_result.scalar_one_or_none()
    if not language:
        raise HTTPException(status_code=400, detail="Invalid language code")

    participant.current_language_id = language.id
    await db.flush()

    return {"message": f"Language updated to {language.name}"}
