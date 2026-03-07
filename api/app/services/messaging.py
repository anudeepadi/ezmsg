"""Messaging service for sending SMS and push notifications.

Provides a unified interface for sending messages via Twilio SMS
and Firebase Cloud Messaging (FCM). Used by admin endpoints for
test sends and direct messaging.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SendResult:
    """Result of a message send attempt."""

    success: bool
    channel: str
    external_id: Optional[str] = None
    error: Optional[str] = None


async def send_sms(phone_number: str, message_text: str) -> SendResult:
    """Send an SMS via Twilio.

    Args:
        phone_number: E.164 formatted phone number (e.g., +15551234567)
        message_text: Message body

    Returns:
        SendResult with Twilio message SID on success.
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return SendResult(
            success=False,
            channel="twilio",
            error="Twilio credentials not configured",
        )

    if not settings.twilio_phone_number:
        return SendResult(
            success=False,
            channel="twilio",
            error="Twilio phone number not configured",
        )

    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(
            body=message_text,
            from_=settings.twilio_phone_number,
            to=phone_number,
        )
        logger.info("SMS sent: SID=%s to=%s", message.sid, phone_number)
        return SendResult(
            success=True,
            channel="twilio",
            external_id=message.sid,
        )
    except ImportError:
        return SendResult(
            success=False,
            channel="twilio",
            error="twilio package not installed",
        )
    except Exception as e:
        logger.error("Failed to send SMS to %s: %s", phone_number, e)
        return SendResult(
            success=False,
            channel="twilio",
            error=str(e),
        )


async def send_push(
    fcm_token: str,
    message_text: str,
    title: str = "EzMsg",
    node_id: Optional[int] = None,
    quick_replies: Optional[list] = None,
) -> SendResult:
    """Send a push notification via Firebase Cloud Messaging.

    Args:
        fcm_token: Device FCM registration token
        message_text: Notification body
        title: Notification title
        node_id: Optional node ID for deep linking
        quick_replies: Optional quick reply buttons

    Returns:
        SendResult with FCM message ID on success.
    """
    try:
        import firebase_admin
        from firebase_admin import messaging
    except ImportError:
        return SendResult(
            success=False,
            channel="fcm",
            error="firebase-admin package not installed",
        )

    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            if settings.firebase_credentials_path:
                cred = firebase_admin.credentials.Certificate(
                    settings.firebase_credentials_path
                )
                firebase_admin.initialize_app(cred)
            else:
                return SendResult(
                    success=False,
                    channel="fcm",
                    error="Firebase credentials not configured",
                )

        data_payload = {}
        if node_id is not None:
            data_payload["node_id"] = str(node_id)
        if quick_replies:
            data_payload["quick_replies"] = json.dumps(quick_replies)

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message_text,
            ),
            data=data_payload if data_payload else None,
            token=fcm_token,
        )
        response = messaging.send(message)
        logger.info("FCM push sent: response=%s", response)
        return SendResult(
            success=True,
            channel="fcm",
            external_id=response,
        )
    except Exception as e:
        logger.error("Failed to send FCM push: %s", e)
        return SendResult(
            success=False,
            channel="fcm",
            error=str(e),
        )


async def send_to_participant(
    phone_number: Optional[str],
    fcm_token: Optional[str],
    channel_type: str,
    message_text: str,
    title: str = "EzMsg",
    node_id: Optional[int] = None,
    quick_replies: Optional[list] = None,
) -> SendResult:
    """Send a message to a participant via their preferred channel.

    Routes to SMS or FCM based on the channel_type.

    Args:
        phone_number: Participant phone number (for Twilio)
        fcm_token: Participant FCM token (for push)
        channel_type: "TWILIO" or "MOBILE_APP"
        message_text: Message body
        title: Push notification title
        node_id: Optional node ID
        quick_replies: Optional quick replies

    Returns:
        SendResult from the appropriate channel.
    """
    if channel_type == "TWILIO":
        if not phone_number:
            return SendResult(
                success=False,
                channel="twilio",
                error="Participant has no phone number",
            )
        return await send_sms(phone_number, message_text)

    # Default to FCM push
    if not fcm_token:
        return SendResult(
            success=False,
            channel="fcm",
            error="Participant has no FCM token",
        )
    return await send_push(
        fcm_token,
        message_text,
        title=title,
        node_id=node_id,
        quick_replies=quick_replies,
    )
