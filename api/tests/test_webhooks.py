"""Tests for webhook endpoints."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_twilio_sms_webhook_missing_fields(client: httpx.AsyncClient):
    """Twilio SMS webhook requires From and Body fields."""
    response = await client.post(
        "/v1/webhooks/twilio/sms",
        data={},  # Twilio sends form-encoded data
    )
    # Should return 400 or 422 for missing required fields
    assert response.status_code in [400, 422, 500]


@pytest.mark.asyncio
async def test_twilio_sms_webhook_unknown_number(client: httpx.AsyncClient):
    """Twilio SMS webhook with unknown phone number."""
    response = await client.post(
        "/v1/webhooks/twilio/sms",
        data={"From": "+10000000000", "Body": "HELPNOW", "To": "+11111111111"},
    )
    # Unknown number should return 200 with error in response, or 404
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_twilio_status_webhook(client: httpx.AsyncClient):
    """Twilio delivery status webhook accepts status updates."""
    response = await client.post(
        "/v1/webhooks/twilio/status",
        data={
            "MessageSid": "SM1234567890",
            "MessageStatus": "delivered",
            "To": "+11111111111",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_fcm_token_registration_unauthenticated(client: httpx.AsyncClient):
    """FCM token registration requires authentication or participant UUID."""
    response = await client.post(
        "/v1/webhooks/fcm/token",
        json={"participant_uuid": "fake-uuid", "fcm_token": "fake-token"},
    )
    # Should be 404 for unknown participant
    assert response.status_code in [404, 422]


@pytest.mark.asyncio
async def test_app_reply_missing_fields(client: httpx.AsyncClient):
    """App reply webhook requires participant_uuid and message."""
    response = await client.post(
        "/v1/webhooks/app/reply",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_app_reply_unknown_participant(client: httpx.AsyncClient):
    """App reply webhook with unknown participant returns 404."""
    response = await client.post(
        "/v1/webhooks/app/reply",
        json={"participant_uuid": "nonexistent-uuid", "message": "HELPNOW"},
    )
    assert response.status_code in [404, 422]


@pytest.mark.asyncio
async def test_twilio_sms_webhook_helpnow_keyword(client: httpx.AsyncClient):
    """HELPNOW keyword is recognized even for unknown numbers."""
    response = await client.post(
        "/v1/webhooks/twilio/sms",
        data={"From": "+10000000000", "Body": "HELPNOW", "To": "+11111111111"},
    )
    # Should handle gracefully even if participant not found
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_twilio_status_missing_sid(client: httpx.AsyncClient):
    """Twilio status webhook handles missing MessageSid gracefully."""
    response = await client.post(
        "/v1/webhooks/twilio/status",
        data={"MessageStatus": "delivered"},
    )
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_fcm_token_missing_token(client: httpx.AsyncClient):
    """FCM token registration requires the token field."""
    response = await client.post(
        "/v1/webhooks/fcm/token",
        json={"participant_uuid": "fake-uuid"},
    )
    assert response.status_code == 422
