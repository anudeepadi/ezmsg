"""Webhooks router for inbound message handling."""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db
from app.rate_limit import limiter
from app.models.participant import Participant, ParticipantStatus
from app.models.incoming_message import IncomingMessage
from app.models.participant import MessagingChannelType
from app.models.scheduled_message import ScheduledMessage, ScheduledMessageStatus
from app.models.keyword import SmsKeyword

logger = logging.getLogger(__name__)


def _verify_twilio_signature(request: Request, form_data: dict) -> bool:
    """Verify Twilio request signature if auth token is configured.

    Returns True if verification passes or is not configured.
    """
    if not settings.twilio_auth_token:
        return True  # Skip verification in dev

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Missing X-Twilio-Signature header")
        return False

    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.twilio_auth_token)
        url = str(request.url)
        return validator.validate(url, form_data, signature)
    except ImportError:
        logger.warning("twilio package not installed, skipping signature verification")
        return True
    except Exception as e:
        logger.error("Twilio signature verification error: %s", e)
        return False

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
@limiter.limit("60/minute")
async def twilio_sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """Handle inbound SMS from Twilio."""
    form_data = await request.form()
    form_dict = dict(form_data)

    # Verify Twilio signature in production
    if settings.is_production and not _verify_twilio_signature(request, form_dict):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

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
@limiter.limit("120/minute")
async def twilio_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Twilio delivery status callbacks."""
    form_data = await request.form()

    # Verify Twilio signature in production
    if settings.is_production:
        form_dict = dict(form_data)
        if not _verify_twilio_signature(request, form_dict):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

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
@limiter.limit("30/minute")
async def fcm_token_refresh(
    request: Request,
    data: FcmTokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle FCM token refresh from mobile app."""
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
@limiter.limit("60/minute")
async def app_reply_webhook(
    request: Request,
    data: AppReplyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle quick reply from mobile app."""
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
        # HELPNOW rotating message pool support
        response_template_id = keyword.response_template_id
        if keyword.message_pool and isinstance(keyword.message_pool, list) and keyword.message_pool:
            # Rotate through the pool using a counter in participant extra_data
            pool = keyword.message_pool
            pool_key = f"helpnow_{keyword.keyword_name.lower()}_index"
            extra = dict(participant.extra_data or {})
            idx = extra.get(pool_key, 0) % len(pool)
            response_template_id = pool[idx]
            extra[pool_key] = idx + 1
            participant.extra_data = extra
            await db.flush()
            logger.info(
                "HELPNOW pool %s: template_id=%d (index %d/%d) for participant %d",
                keyword.keyword_name, response_template_id, idx, len(pool), participant.id,
            )

        return {
            "matched": True,
            "action": "help_requested",
            "response_template_id": response_template_id,
        }

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
