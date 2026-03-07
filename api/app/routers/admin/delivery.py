"""Admin delivery management - message queue monitoring and test sends."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.participant import Participant, MessagingChannelType
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageStatus
from app.security.deps import require_admin
from app.models.user import User
from app.services.messaging import send_to_participant, SendResult

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_admin)])


# ── Response schemas ─────────────────────────────────────────────────


class QueueStats(BaseModel):
    """Message queue statistics."""

    pending: int
    in_progress: int
    sent: int
    failed: int
    skipped: int
    aborted: int
    total: int


class MessageSummary(BaseModel):
    """Scheduled message summary for listing."""

    id: int
    participant_id: int
    participant_uuid: Optional[str] = None
    project_id: int
    messaging_node_id: Optional[int] = None
    template_id: Optional[int] = None
    status: str
    channel_type: str
    message_body: Optional[str] = None
    send_at: datetime
    sent_at: Optional[datetime] = None
    attempt_count: int
    last_error_message: Optional[str] = None
    external_id: Optional[str] = None
    created_at: Optional[datetime] = None


class MessageListResponse(BaseModel):
    """Paginated message list."""

    messages: list[MessageSummary]
    total: int
    page: int
    limit: int


class TestSendRequest(BaseModel):
    """Request to send a test message."""

    participant_id: int
    message_text: str
    channel_override: Optional[str] = None  # "TWILIO" or "MOBILE_APP"


class TestSendResponse(BaseModel):
    """Result of a test send."""

    success: bool
    channel: str
    external_id: Optional[str] = None
    error: Optional[str] = None


class ChannelStatusResponse(BaseModel):
    """Channel configuration status."""

    twilio_configured: bool
    twilio_phone_number: str
    fcm_configured: bool
    simulation_mode: bool


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/project/{project_id}/stats", response_model=QueueStats)
async def get_queue_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> QueueStats:
    """Get message queue statistics for a project."""
    result = await db.execute(
        select(
            ScheduledMessage.status,
            func.count(ScheduledMessage.id),
        )
        .where(ScheduledMessage.project_id == project_id)
        .group_by(ScheduledMessage.status)
    )

    counts: dict[str, int] = {}
    for row in result:
        counts[row[0].value if hasattr(row[0], "value") else str(row[0])] = row[1]

    return QueueStats(
        pending=counts.get("PENDING", 0),
        in_progress=counts.get("IN_PROGRESS", 0),
        sent=counts.get("SENT", 0),
        failed=counts.get("FAILED", 0),
        skipped=counts.get("SKIPPED", 0),
        aborted=counts.get("ABORTED", 0),
        total=sum(counts.values()),
    )


@router.get("/project/{project_id}/messages", response_model=MessageListResponse)
async def list_messages(
    project_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    participant_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """List scheduled messages with filtering and pagination."""
    conditions = [ScheduledMessage.project_id == project_id]

    if status_filter:
        try:
            status_enum = ScheduledMessageStatus(status_filter.upper())
            conditions.append(ScheduledMessage.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_filter}",
            )

    if channel:
        try:
            channel_enum = MessagingChannelType(channel.upper())
            conditions.append(ScheduledMessage.channel_type == channel_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid channel: {channel}",
            )

    if participant_id:
        conditions.append(ScheduledMessage.participant_id == participant_id)

    # Count total
    count_result = await db.execute(
        select(func.count(ScheduledMessage.id)).where(and_(*conditions))
    )
    total = count_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * limit
    result = await db.execute(
        select(ScheduledMessage)
        .where(and_(*conditions))
        .order_by(ScheduledMessage.send_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()

    # Get participant UUIDs for display
    participant_ids = {m.participant_id for m in messages}
    uuid_map: dict[int, str] = {}
    if participant_ids:
        p_result = await db.execute(
            select(Participant.id, Participant.uu_id).where(
                Participant.id.in_(participant_ids)
            )
        )
        uuid_map = {row[0]: row[1] for row in p_result}

    summaries = [
        MessageSummary(
            id=m.id,
            participant_id=m.participant_id,
            participant_uuid=uuid_map.get(m.participant_id),
            project_id=m.project_id,
            messaging_node_id=m.messaging_node_id,
            template_id=m.template_id,
            status=m.status.value if hasattr(m.status, "value") else str(m.status),
            channel_type=(
                m.channel_type.value
                if hasattr(m.channel_type, "value")
                else str(m.channel_type)
            ),
            message_body=m.message_body[:200] if m.message_body else None,
            send_at=m.send_at,
            sent_at=m.sent_at,
            attempt_count=m.attempt_count,
            last_error_message=m.last_error_message,
            external_id=m.external_id,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return MessageListResponse(
        messages=summaries,
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/test-send", response_model=TestSendResponse)
async def test_send_message(
    data: TestSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TestSendResponse:
    """Send a test message to a participant.

    Bypasses the scheduler queue and sends directly via the
    appropriate channel. Useful for testing delivery configuration.
    """
    # Load participant
    result = await db.execute(
        select(Participant).where(
            Participant.id == data.participant_id,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )

    channel = data.channel_override or (
        participant.channel_type.value
        if hasattr(participant.channel_type, "value")
        else str(participant.channel_type)
    )

    logger.info(
        "Admin %s sending test message to participant %d via %s",
        current_user.email,
        participant.id,
        channel,
    )

    send_result: SendResult = await send_to_participant(
        phone_number=participant.phone_number,
        fcm_token=participant.fcm_token,
        channel_type=channel,
        message_text=data.message_text,
        title="EzMsg Test",
    )

    # Log the test send as a scheduled message for audit trail
    test_msg = ScheduledMessage(
        project_id=participant.project_id,
        participant_id=participant.id,
        status=(
            ScheduledMessageStatus.SENT
            if send_result.success
            else ScheduledMessageStatus.FAILED
        ),
        message_body=data.message_text,
        send_at=datetime.now(timezone.utc),
        sent_at=datetime.now(timezone.utc) if send_result.success else None,
        channel_type=MessagingChannelType(channel),
        external_id=send_result.external_id,
        last_error_message=send_result.error,
        extra_data={"type": "test_send", "sent_by": current_user.email},
    )
    db.add(test_msg)
    await db.flush()

    return TestSendResponse(
        success=send_result.success,
        channel=send_result.channel,
        external_id=send_result.external_id,
        error=send_result.error,
    )


@router.get("/channel-status", response_model=ChannelStatusResponse)
async def get_channel_status() -> ChannelStatusResponse:
    """Check which delivery channels are configured."""
    from app.config import settings

    return ChannelStatusResponse(
        twilio_configured=bool(
            settings.twilio_account_sid and settings.twilio_auth_token
        ),
        twilio_phone_number=settings.twilio_phone_number or "",
        fcm_configured=bool(settings.firebase_credentials_path),
        simulation_mode=settings.simulation_mode,
    )


@router.post("/project/{project_id}/retry-failed")
async def retry_failed_messages(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Reset all FAILED messages back to PENDING for retry.

    Only resets messages that haven't exceeded max_attempts.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        text("""
            UPDATE scheduled_messages
            SET status = 'PENDING',
                locked_by = NULL,
                locked_at = NULL,
                updated_at = :now
            WHERE project_id = :project_id
              AND status = 'FAILED'
              AND attempt_count < max_attempts
            RETURNING id
        """),
        {"project_id": project_id, "now": now},
    )
    retried_ids = [row[0] for row in result.fetchall()]

    logger.info(
        "Admin %s retried %d failed messages in project %d",
        current_user.email,
        len(retried_ids),
        project_id,
    )

    return {"retried_count": len(retried_ids)}
