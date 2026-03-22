"""Scheduler router for worker control endpoints."""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageStatus
from app.models.participant import Participant
from app.models.user import User
from app.security.deps import get_current_active_user, require_admin

router = APIRouter()


class QueueHealth(BaseModel):
    """Queue health status."""
    pending_count: int
    in_progress_count: int
    failed_count: int
    sent_today: int
    oldest_pending_minutes: Optional[float]


class ScheduledMessageResponse(BaseModel):
    """Scheduled message response."""
    id: int
    participant_id: int
    node_id: int
    status: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    attempt_count: int
    error_message: Optional[str]


class RequeueResult(BaseModel):
    """Requeue operation result."""
    requeued_count: int
    message: str


class AbortResult(BaseModel):
    """Abort operation result."""
    aborted_count: int
    message: str


@router.get("/health", response_model=QueueHealth)
async def get_queue_health(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> QueueHealth:
    """Get scheduler queue health metrics.

    Args:
        db: Database session
        user: Current user

    Returns:
        Queue health metrics
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Count pending
    pending_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.status == ScheduledMessageStatus.PENDING
        )
    )
    pending_count = pending_result.scalar() or 0

    # Count in progress
    in_progress_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.status == ScheduledMessageStatus.IN_PROGRESS
        )
    )
    in_progress_count = in_progress_result.scalar() or 0

    # Count failed
    failed_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.status == ScheduledMessageStatus.FAILED
        )
    )
    failed_count = failed_result.scalar() or 0

    # Count sent today
    sent_today_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(
            ScheduledMessage.status == ScheduledMessageStatus.SENT,
            ScheduledMessage.sent_at >= today_start,
        )
    )
    sent_today = sent_today_result.scalar() or 0

    # Find oldest pending
    oldest_result = await db.execute(
        select(func.min(ScheduledMessage.send_at)).where(
            ScheduledMessage.status == ScheduledMessageStatus.PENDING,
            ScheduledMessage.send_at <= now,
        )
    )
    oldest_pending = oldest_result.scalar()
    oldest_pending_minutes = None
    if oldest_pending:
        delta = now - oldest_pending
        oldest_pending_minutes = delta.total_seconds() / 60

    return QueueHealth(
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        failed_count=failed_count,
        sent_today=sent_today,
        oldest_pending_minutes=oldest_pending_minutes,
    )


@router.post("/poll")
async def trigger_poll(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """Trigger a manual poll iteration.

    This is primarily for debugging/testing. In production,
    the worker runs continuously.

    Args:
        db: Database session
        user: Admin user

    Returns:
        Poll result
    """
    # This would normally trigger the worker
    # For now, just return status
    return {
        "message": "Poll triggered",
        "note": "Worker handles actual processing",
    }


@router.post("/requeue", response_model=RequeueResult)
async def requeue_failed(
    max_age_hours: int = 24,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> RequeueResult:
    """Requeue failed messages for retry.

    Args:
        max_age_hours: Only requeue messages failed within this many hours
        db: Database session
        user: Admin user

    Returns:
        Requeue result
    """
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    cutoff = now - timedelta(hours=max_age_hours)

    # Update failed messages to pending
    result = await db.execute(
        update(ScheduledMessage)
        .where(
            ScheduledMessage.status == ScheduledMessageStatus.FAILED,
            ScheduledMessage.updated_at >= cutoff,
        )
        .values(
            status=ScheduledMessageStatus.PENDING,
            attempt_count=0,
            last_error_message=None,
            last_error_code=None,
        )
    )

    requeued_count = result.rowcount

    return RequeueResult(
        requeued_count=requeued_count,
        message=f"Requeued {requeued_count} failed messages",
    )


@router.post("/abort/participant/{participant_id}", response_model=AbortResult)
async def abort_participant_messages(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> AbortResult:
    """Abort all pending messages for a participant.

    Args:
        participant_id: Participant ID
        db: Database session
        user: Admin user

    Returns:
        Abort result
    """
    # Verify participant exists
    participant_result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = participant_result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Abort pending messages
    result = await db.execute(
        update(ScheduledMessage)
        .where(
            ScheduledMessage.participant_id == participant_id,
            ScheduledMessage.status == ScheduledMessageStatus.PENDING,
        )
        .values(status=ScheduledMessageStatus.ABORTED)
    )

    aborted_count = result.rowcount

    return AbortResult(
        aborted_count=aborted_count,
        message=f"Aborted {aborted_count} pending messages for participant {participant_id}",
    )


@router.post("/abort/project/{project_id}", response_model=AbortResult)
async def abort_project_messages(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> AbortResult:
    """Abort all pending messages for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Admin user

    Returns:
        Abort result
    """
    # Abort pending messages
    result = await db.execute(
        update(ScheduledMessage)
        .where(
            ScheduledMessage.project_id == project_id,
            ScheduledMessage.status == ScheduledMessageStatus.PENDING,
        )
        .values(status=ScheduledMessageStatus.ABORTED)
    )

    aborted_count = result.rowcount

    return AbortResult(
        aborted_count=aborted_count,
        message=f"Aborted {aborted_count} pending messages for project {project_id}",
    )


@router.get("/messages/pending", response_model=List[ScheduledMessageResponse])
async def list_pending_messages(
    project_id: Optional[int] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> List[ScheduledMessageResponse]:
    """List pending scheduled messages.

    Args:
        project_id: Optional project filter
        limit: Max results
        db: Database session
        user: Current user

    Returns:
        List of pending messages
    """
    query = select(ScheduledMessage).where(
        ScheduledMessage.status == ScheduledMessageStatus.PENDING
    )

    if project_id:
        query = query.where(ScheduledMessage.project_id == project_id)

    query = query.order_by(ScheduledMessage.send_at).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        ScheduledMessageResponse(
            id=m.id,
            participant_id=m.participant_id,
            node_id=m.messaging_node_id or 0,
            status=m.status.value,
            scheduled_at=m.send_at,
            sent_at=m.sent_at,
            attempt_count=m.attempt_count,
            error_message=m.last_error_message,
        )
        for m in messages
    ]


@router.get("/messages/failed", response_model=List[ScheduledMessageResponse])
async def list_failed_messages(
    project_id: Optional[int] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> List[ScheduledMessageResponse]:
    """List failed scheduled messages.

    Args:
        project_id: Optional project filter
        limit: Max results
        db: Database session
        user: Current user

    Returns:
        List of failed messages
    """
    query = select(ScheduledMessage).where(
        ScheduledMessage.status == ScheduledMessageStatus.FAILED
    )

    if project_id:
        query = query.where(ScheduledMessage.project_id == project_id)

    query = query.order_by(ScheduledMessage.updated_at.desc()).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        ScheduledMessageResponse(
            id=m.id,
            participant_id=m.participant_id,
            node_id=m.messaging_node_id or 0,
            status=m.status.value,
            scheduled_at=m.send_at,
            sent_at=m.sent_at,
            attempt_count=m.attempt_count,
            error_message=m.last_error_message,
        )
        for m in messages
    ]
