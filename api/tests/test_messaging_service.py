"""Tests for the messaging service module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.messaging import send_sms, send_push, send_to_participant, SendResult


@pytest.mark.asyncio
async def test_send_sms_no_credentials():
    """SMS send fails gracefully when Twilio credentials are not configured."""
    with patch("app.services.messaging.settings") as mock_settings:
        mock_settings.twilio_account_sid = ""
        mock_settings.twilio_auth_token = ""
        result = await send_sms("+15551234567", "Test message")
    assert not result.success
    assert result.channel == "twilio"
    assert "not configured" in result.error


@pytest.mark.asyncio
async def test_send_sms_no_phone_number():
    """SMS send fails when Twilio phone number is not configured."""
    with patch("app.services.messaging.settings") as mock_settings:
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"
        mock_settings.twilio_phone_number = ""
        result = await send_sms("+15551234567", "Test message")
    assert not result.success
    assert "phone number not configured" in result.error


@pytest.mark.asyncio
async def test_send_sms_twilio_not_installed():
    """SMS send fails gracefully when twilio package is not installed."""
    with patch("app.services.messaging.settings") as mock_settings:
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"
        mock_settings.twilio_phone_number = "+15550001111"

        with patch.dict("sys.modules", {"twilio": None, "twilio.rest": None}):
            result = await send_sms("+15551234567", "Test message")

    assert not result.success
    assert result.channel == "twilio"


@pytest.mark.asyncio
async def test_send_push_no_firebase():
    """FCM push fails gracefully when firebase package is not installed."""
    with patch.dict("sys.modules", {"firebase_admin": None}):
        result = await send_push("fake_token", "Test message")
    assert not result.success
    assert result.channel == "fcm"


@pytest.mark.asyncio
async def test_send_to_participant_twilio_no_phone():
    """send_to_participant returns error when Twilio channel has no phone number."""
    result = await send_to_participant(
        phone_number=None,
        fcm_token="fake_token",
        channel_type="TWILIO",
        message_text="Hello",
    )
    assert not result.success
    assert "no phone number" in result.error


@pytest.mark.asyncio
async def test_send_to_participant_fcm_no_token():
    """send_to_participant returns error when FCM channel has no token."""
    result = await send_to_participant(
        phone_number="+15551234567",
        fcm_token=None,
        channel_type="MOBILE_APP",
        message_text="Hello",
    )
    assert not result.success
    assert "no FCM token" in result.error


@pytest.mark.asyncio
async def test_send_to_participant_routes_to_sms():
    """send_to_participant routes TWILIO channel to send_sms."""
    with patch("app.services.messaging.send_sms") as mock_sms:
        mock_sms.return_value = SendResult(
            success=True, channel="twilio", external_id="SM123"
        )
        result = await send_to_participant(
            phone_number="+15551234567",
            fcm_token=None,
            channel_type="TWILIO",
            message_text="Hello",
        )
    assert result.success
    assert result.channel == "twilio"
    mock_sms.assert_called_once_with("+15551234567", "Hello")


@pytest.mark.asyncio
async def test_send_to_participant_routes_to_fcm():
    """send_to_participant routes MOBILE_APP channel to send_push."""
    with patch("app.services.messaging.send_push") as mock_push:
        mock_push.return_value = SendResult(
            success=True, channel="fcm", external_id="msg-123"
        )
        result = await send_to_participant(
            phone_number=None,
            fcm_token="fake_token",
            channel_type="MOBILE_APP",
            message_text="Hello",
            title="Test",
        )
    assert result.success
    assert result.channel == "fcm"
    mock_push.assert_called_once_with(
        "fake_token", "Hello", title="Test", node_id=None, quick_replies=None
    )


def test_send_result_is_immutable():
    """SendResult is a frozen dataclass."""
    result = SendResult(success=True, channel="twilio", external_id="SM123")
    with pytest.raises(AttributeError):
        result.success = False  # type: ignore
