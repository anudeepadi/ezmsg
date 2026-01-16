"""Participants admin router."""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.participant import Participant, ParticipantStatus, MessagingChannelType
from app.models.project import Project
from app.models.user import User
from app.security.deps import get_current_active_user

router = APIRouter()


class ParticipantCreate(BaseModel):
    """Participant creation schema."""
    project_id: int
    external_id: Optional[str] = None
    phone_number: Optional[str] = None
    fcm_token: Optional[str] = None
    channel_type: str = "MOBILE_APP"
    language_id: int = 1
    is_test_participant: bool = False


class ParticipantUpdate(BaseModel):
    """Participant update schema."""
    status: Optional[str] = None
    phone_number: Optional[str] = None
    fcm_token: Optional[str] = None
    language_id: Optional[int] = None


class ParticipantResponse(BaseModel):
    """Participant response schema."""
    id: int
    uu_id: Optional[str]
    project_id: int
    external_id: Optional[str]
    status: str
    channel_type: str
    language_id: int
    is_test_participant: bool
    enrolled_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ParticipantListResponse(BaseModel):
    """Paginated participant list response."""
    items: List[ParticipantResponse]
    total: int
    page: int
    size: int


@router.get("/project/{project_id}", response_model=ParticipantListResponse)
async def list_participants(
    project_id: int,
    page: int = 1,
    size: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ParticipantListResponse:
    """List participants for a project.

    Args:
        project_id: Project ID
        page: Page number
        size: Page size
        status_filter: Optional status filter
        db: Database session
        user: Current user

    Returns:
        Paginated list of participants
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build query
    query = select(Participant).where(
        Participant.project_id == project_id,
        Participant.removed_at.is_(None),
    )

    if status_filter:
        try:
            status_enum = ParticipantStatus(status_filter)
            query = query.where(Participant.status == status_enum)
        except ValueError:
            pass

    # Count
    count_query = select(func.count(Participant.id)).where(
        Participant.project_id == project_id,
        Participant.removed_at.is_(None),
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Paginate
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Participant.created_at.desc())

    result = await db.execute(query)
    participants = result.scalars().all()

    items = [
        ParticipantResponse(
            id=p.id,
            uu_id=p.uu_id,
            project_id=p.project_id,
            external_id=p.external_id,
            status=p.status.value,
            channel_type=p.channel_type.value,
            language_id=p.current_language_id,
            is_test_participant=p.is_test_participant,
            enrolled_at=p.enrolled_at,
            completed_at=p.completed_at,
            created_at=p.created_at,
        )
        for p in participants
    ]

    return ParticipantListResponse(items=items, total=total, page=page, size=size)


@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def create_participant(
    data: ParticipantCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ParticipantResponse:
    """Create a new participant.

    Args:
        data: Participant data
        db: Database session
        user: Current user

    Returns:
        Created participant
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == data.project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        channel = MessagingChannelType(data.channel_type)
    except ValueError:
        channel = MessagingChannelType.MOBILE_APP

    participant = Participant(
        project_id=data.project_id,
        external_id=data.external_id,
        phone_number=data.phone_number,
        fcm_token=data.fcm_token,
        channel_type=channel,
        current_language_id=data.language_id,
        is_test_participant=data.is_test_participant,
        status=ParticipantStatus.ACTIVE,
        enrolled_at=datetime.now(timezone.utc),
    )
    db.add(participant)
    await db.flush()
    await db.refresh(participant)

    return ParticipantResponse(
        id=participant.id,
        uu_id=participant.uu_id,
        project_id=participant.project_id,
        external_id=participant.external_id,
        status=participant.status.value,
        channel_type=participant.channel_type.value,
        language_id=participant.current_language_id,
        is_test_participant=participant.is_test_participant,
        enrolled_at=participant.enrolled_at,
        completed_at=participant.completed_at,
        created_at=participant.created_at,
    )


@router.get("/{participant_id}", response_model=ParticipantResponse)
async def get_participant(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ParticipantResponse:
    """Get a specific participant.

    Args:
        participant_id: Participant ID
        db: Database session
        user: Current user

    Returns:
        Participant details
    """
    result = await db.execute(
        select(Participant)
        .options(selectinload(Participant.project))
        .where(Participant.id == participant_id, Participant.removed_at.is_(None))
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if user.role.value != "admin" and participant.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ParticipantResponse(
        id=participant.id,
        uu_id=participant.uu_id,
        project_id=participant.project_id,
        external_id=participant.external_id,
        status=participant.status.value,
        channel_type=participant.channel_type.value,
        language_id=participant.current_language_id,
        is_test_participant=participant.is_test_participant,
        enrolled_at=participant.enrolled_at,
        completed_at=participant.completed_at,
        created_at=participant.created_at,
    )


@router.put("/{participant_id}", response_model=ParticipantResponse)
async def update_participant(
    participant_id: int,
    data: ParticipantUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ParticipantResponse:
    """Update a participant.

    Args:
        participant_id: Participant ID
        data: Update data
        db: Database session
        user: Current user

    Returns:
        Updated participant
    """
    result = await db.execute(
        select(Participant)
        .options(selectinload(Participant.project))
        .where(Participant.id == participant_id, Participant.removed_at.is_(None))
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if user.role.value != "admin" and participant.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if data.status:
        try:
            participant.status = ParticipantStatus(data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")

    if data.phone_number is not None:
        participant.phone_number = data.phone_number
    if data.fcm_token is not None:
        participant.fcm_token = data.fcm_token
    if data.language_id is not None:
        participant.current_language_id = data.language_id

    await db.flush()
    await db.refresh(participant)

    return ParticipantResponse(
        id=participant.id,
        uu_id=participant.uu_id,
        project_id=participant.project_id,
        external_id=participant.external_id,
        status=participant.status.value,
        channel_type=participant.channel_type.value,
        language_id=participant.current_language_id,
        is_test_participant=participant.is_test_participant,
        enrolled_at=participant.enrolled_at,
        completed_at=participant.completed_at,
        created_at=participant.created_at,
    )
