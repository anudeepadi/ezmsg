"""Webhooks router for inbound message handling."""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.participant import Participant, ParticipantStatus
from app.models.incoming_message import IncomingMessage
from app.models.participant import MessagingChannelType
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageStatus
from app.models.keyword import SmsKeyword

router = APIRouter()


class AppReplyRequest(BaseModel):
    """App quick reply request."""
    participant_uuid: str
    reply_text: str
    node_id: Optional[int] = None


class FcmTokenRefresh(BaseModel):
    """FCM token refresh request."""
    participant_uuid: str
    old_token: Optional[str] = None
    new_token: str


@router.post("/twilio/sms")
async def twilio_sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """Handle inbound SMS from Twilio.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        TwiML response
    """
    form_data = await request.form()

    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")
    body = form_data.get("Body", "")
    message_sid = form_data.get("MessageSid", "")

    # Find participant by phone number
    participant_result = await db.execute(
        select(Participant).where(
            Participant.phone_number == from_number,
            Participant.removed_at.is_(None),
        )
    )
    participant = participant_result.scalar_one_or_none()

    # Store incoming message
    incoming = IncomingMessage(
        participant_id=participant.id if participant else None,
        channel_type=MessagingChannelType.TWILIO,
        from_address=from_number,
        to_address=to_number,
        body=body,
        external_id=message_sid,
        received_at=datetime.now(timezone.utc),
    )
    db.add(incoming)
    await db.flush()

    # Process keywords if participant found
    if participant and body:
        await _process_keywords(db, participant, body.strip().upper())

    # Return empty TwiML response
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


@router.post("/twilio/status")
async def twilio_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Twilio delivery status callbacks.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Acknowledgment
    """
    form_data = await request.form()

    message_sid = form_data.get("MessageSid", "")
    status = form_data.get("MessageStatus", "")
    error_code = form_data.get("ErrorCode")
    error_message = form_data.get("ErrorMessage")

    # Find scheduled message by external ID
    result = await db.execute(
        select(ScheduledMessage).where(
            ScheduledMessage.external_id == message_sid
        )
    )
    message = result.scalar_one_or_none()

    if message:
        if status in ("delivered", "sent"):
            message.status = ScheduledMessageStatus.SENT
            message.sent_at = datetime.now(timezone.utc)
        elif status in ("failed", "undelivered"):
            message.status = ScheduledMessageStatus.FAILED
            message.last_error_message = f"{error_code}: {error_message}" if error_code else error_message
        await db.flush()

    return {"status": "received"}


@router.post("/fcm/token")
async def fcm_token_refresh(
    data: FcmTokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle FCM token refresh from mobile app.

    Args:
        data: Token refresh data
        db: Database session

    Returns:
        Acknowledgment
    """
    result = await db.execute(
        select(Participant).where(
            Participant.uu_id == data.participant_uuid,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    participant.fcm_token = data.new_token
    await db.flush()

    return {"status": "updated"}


@router.post("/app/reply")
async def app_reply_webhook(
    data: AppReplyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle quick reply from mobile app.

    Args:
        data: Reply data
        db: Database session

    Returns:
        Response with any triggered actions
    """
    # Find participant
    result = await db.execute(
        select(Participant).where(
            Participant.uu_id == data.participant_uuid,
            Participant.removed_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Store incoming message
    incoming = IncomingMessage(
        participant_id=participant.id,
        channel_type=MessagingChannelType.MOBILE_APP,
        from_address=data.participant_uuid,
        body=data.reply_text,
        quick_reply_value=data.reply_text,
        received_at=datetime.now(timezone.utc),
    )
    db.add(incoming)
    await db.flush()

    # Process as keyword
    keyword_result = await _process_keywords(
        db, participant, data.reply_text.strip().upper()
    )

    return {
        "status": "received",
        "keyword_matched": keyword_result.get("matched", False),
        "action": keyword_result.get("action"),
    }


async def _process_keywords(
    db: AsyncSession,
    participant: Participant,
    text: str,
) -> dict:
    """Process incoming text for keyword matches.

    Args:
        db: Database session
        participant: Participant model
        text: Incoming text (uppercase)

    Returns:
        Processing result
    """
    # Check for project-specific keywords
    keyword_result = await db.execute(
        select(SmsKeyword).where(
            SmsKeyword.project_id == participant.project_id,
            SmsKeyword.keyword_text == text,
            SmsKeyword.is_active == True,
            SmsKeyword.removed_at.is_(None),
        )
    )
    keyword = keyword_result.scalar_one_or_none()

    if not keyword:
        return {"matched": False}

    # Process keyword action based on keyword_action_type
    action = keyword.keyword_action_type.upper() if keyword.keyword_action_type else ""

    if action == "STOP" or text in ("STOP", "EXIT", "QUIT", "CANCEL"):
        # Opt out participant
        participant.status = ParticipantStatus.INACTIVE

        # Abort pending messages
        await db.execute(
            update(ScheduledMessage)
            .where(
                ScheduledMessage.participant_id == participant.id,
                ScheduledMessage.status == ScheduledMessageStatus.PENDING,
            )
            .values(status=ScheduledMessageStatus.ABORTED)
        )
        await db.flush()

        return {"matched": True, "action": "opt_out"}

    elif action == "HELP" or text in ("HELP", "HELPNOW", "INFO"):
        # Could trigger help response
        return {"matched": True, "action": "help_requested"}

    elif action == "PAUSE":
        participant.status = ParticipantStatus.SUSPENDED
        await db.flush()
        return {"matched": True, "action": "paused"}

    elif action == "RESUME":
        if participant.status == ParticipantStatus.SUSPENDED:
            participant.status = ParticipantStatus.ACTIVE
            await db.flush()
        return {"matched": True, "action": "resumed"}

    elif keyword.messaging_node_id:
        # Trigger transition to specific node
        return {
            "matched": True,
            "action": "node_transition",
            "target_node_id": keyword.messaging_node_id,
        }

    return {"matched": True, "action": keyword.keyword_action_type}
