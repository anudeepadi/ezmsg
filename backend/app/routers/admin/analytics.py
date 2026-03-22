"""Analytics admin router."""

from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Project
from app.models.participant import Participant, ParticipantStatus
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageStatus
from app.models.user import User
from app.security.deps import get_current_active_user

router = APIRouter()


class OverviewStats(BaseModel):
    """Overview statistics."""
    total_participants: int
    active_participants: int
    completed_participants: int
    total_messages_sent: int
    messages_pending: int
    messages_failed: int
    delivery_rate: float


class DeliveryStats(BaseModel):
    """Delivery statistics."""
    total_sent: int
    total_pending: int
    total_failed: int
    total_aborted: int
    sent_today: int
    sent_this_week: int


class EngagementStats(BaseModel):
    """Engagement statistics."""
    total_responses: int
    response_rate: float
    avg_response_time_minutes: Optional[float]


@router.get("/project/{project_id}/overview", response_model=OverviewStats)
async def get_project_overview(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> OverviewStats:
    """Get overview statistics for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Overview statistics
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

    # Count participants
    total_participants_result = await db.execute(
        select(func.count(Participant.id)).where(
            Participant.project_id == project_id,
            Participant.removed_at.is_(None),
        )
    )
    total_participants = total_participants_result.scalar() or 0

    active_participants_result = await db.execute(
        select(func.count(Participant.id)).where(
            Participant.project_id == project_id,
            Participant.status == ParticipantStatus.ACTIVE,
            Participant.removed_at.is_(None),
        )
    )
    active_participants = active_participants_result.scalar() or 0

    completed_participants_result = await db.execute(
        select(func.count(Participant.id)).where(
            Participant.project_id == project_id,
            Participant.status == ParticipantStatus.COMPLETED,
            Participant.removed_at.is_(None),
        )
    )
    completed_participants = completed_participants_result.scalar() or 0

    # Count messages
    total_sent_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.SENT,
        )
    )
    total_sent = total_sent_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.PENDING,
        )
    )
    pending = pending_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.FAILED,
        )
    )
    failed = failed_result.scalar() or 0

    # Calculate delivery rate
    total_attempted = total_sent + failed
    delivery_rate = (total_sent / total_attempted * 100) if total_attempted > 0 else 100.0

    return OverviewStats(
        total_participants=total_participants,
        active_participants=active_participants,
        completed_participants=completed_participants,
        total_messages_sent=total_sent,
        messages_pending=pending,
        messages_failed=failed,
        delivery_rate=round(delivery_rate, 2),
    )


@router.get("/project/{project_id}/delivery", response_model=DeliveryStats)
async def get_delivery_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> DeliveryStats:
    """Get delivery statistics for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Delivery statistics
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

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Count by status
    sent_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.SENT,
        )
    )
    total_sent = sent_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.PENDING,
        )
    )
    total_pending = pending_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.FAILED,
        )
    )
    total_failed = failed_result.scalar() or 0

    aborted_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.ABORTED,
        )
    )
    total_aborted = aborted_result.scalar() or 0

    # Sent today
    sent_today_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.SENT,
            ScheduledMessage.sent_at >= today_start,
        )
    )
    sent_today = sent_today_result.scalar() or 0

    # Sent this week
    sent_week_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.SENT,
            ScheduledMessage.sent_at >= week_start,
        )
    )
    sent_this_week = sent_week_result.scalar() or 0

    return DeliveryStats(
        total_sent=total_sent,
        total_pending=total_pending,
        total_failed=total_failed,
        total_aborted=total_aborted,
        sent_today=sent_today,
        sent_this_week=sent_this_week,
    )
