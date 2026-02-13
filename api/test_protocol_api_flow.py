#!/usr/bin/env python3
"""
Test Protocol API Flow - Mobile App Integration Example

This script demonstrates how a mobile app should interact with the
EzMsg Protocol API to guide users through the QuitTxt smoking cessation protocol.

API Endpoints:
- POST /v1/protocol/start     - Start a new session
- POST /v1/protocol/respond   - Send user response
- GET  /v1/protocol/session/{id} - Check session status
- DELETE /v1/protocol/session/{id} - End session

Authentication: X-API-Key header
"""

import asyncio
import httpx
from datetime import datetime
import os
from typing import Optional

# Configuration
API_BASE_URL = os.getenv("EZMSG_PROTOCOL_API_BASE_URL", "http://localhost:8000/v1")
API_KEY = os.getenv("PROTOCOL_API_KEY", "dev-change-me")
PROJECT_ID = 1  # QuitTxt V9 UTSA Study

# Test user responses
TEST_RESPONSES = {
    "INTAKE_STUDY_INFO": "1",  # Continue
    "INTAKE_QUIZ_INTRO": "1",  # Start quiz
    "INTAKE_CPD": "2",  # 11-20 cigarettes per day
    "INTAKE_NICOTINE": "1",  # Yes, using nicotine replacement
    "INTAKE_REASONS": "1",  # Health reasons
    "INTAKE_SUPPORT": "1",  # Have support
    "INTAKE_READY": "YES_TOMORROW",  # Ready to quit tomorrow
    "INTAKE_YES_TIME": "1",  # Morning preference
}


class ProtocolAPIClient:
    """Client for interacting with the Protocol API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    async def start_session(
        self,
        project_id: int,
        language: str = "en",
        initial_response: Optional[str] = None
    ) -> dict:
        """Start a new protocol session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/protocol/start",
                headers=self.headers,
                json={
                    "project_id": project_id,
                    "language": language,
                    "initial_response": initial_response,
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def send_response(self, session_id: str, response_text: str) -> dict:
        """Send a response to continue the protocol."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/protocol/respond",
                headers=self.headers,
                json={
                    "session_id": session_id,
                    "response": response_text,
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_session_status(self, session_id: str) -> dict:
        """Get current session status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/protocol/session/{session_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def end_session(self, session_id: str) -> dict:
        """End and delete a session."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/protocol/session/{session_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()


def print_message(step: int, data: dict):
    """Pretty print a protocol message."""
    message = data["message"]

    print(f"\n{'='*80}")
    print(f"STEP {step}: {data['current_node_name']}")
    print(f"{'='*80}")
    print("\nMessage to user:")
    print(f"   {message['message_text']}")

    if message.get('media_url'):
        print(f"\nMedia: {message['media_url']}")

    if message.get('quick_replies'):
        print("\nQuick reply options:")
        for qr in message['quick_replies']:
            print(f"   [{qr['value']}] {qr['label']}")

    print("\nSession info:")
    print(f"   Session ID: {data['session_id']}")
    print(f"   Node ID: {data['current_node_id']}")
    print(f"   Expects Reply: {message['expects_reply']}")
    print(f"   Is Terminal: {message['is_terminal']}")

    if data.get('next_scheduled_at'):
        next_time = datetime.fromisoformat(data['next_scheduled_at'])
        print(f"   Next Scheduled: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")


async def test_protocol_flow():
    """Test the complete protocol flow."""
    client = ProtocolAPIClient(API_BASE_URL, API_KEY)

    print(f"\n{'#'*80}")
    print("# EzMsg Protocol API Test - Mobile App Integration")
    print(f"{'#'*80}")
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Project ID: {PROJECT_ID} (QuitTxt V9 UTSA Study)")
    print(f"Language: English")

    # Step 1: Start the session
    print(f"\n{'='*80}")
    print("STARTING PROTOCOL SESSION")
    print(f"{'='*80}")

    session_data = await client.start_session(
        project_id=PROJECT_ID,
        language="en"
    )

    session_id = session_data["session_id"]
    step_count = 1

    print_message(step_count, session_data)

    # Step 2: Progress through the protocol
    max_steps = 10  # Limit steps for demo
    current_step = step_count

    while current_step < max_steps:
        message = session_data["message"]

        # Check if we should continue
        if message["is_terminal"]:
            print("\nProtocol complete. Reached terminal node.")
            break

        if not message["expects_reply"]:
            print("\nAuto-advancing to next message...")
            # For time-delayed messages, in a real app you'd wait or poll
            await asyncio.sleep(1)

        # Get response for this node
        node_name = session_data["current_node_name"]

        # Use predefined response or default
        if node_name in TEST_RESPONSES:
            user_response = TEST_RESPONSES[node_name]
        elif message.get("quick_replies"):
            # Use first quick reply
            user_response = message["quick_replies"][0]["value"]
        else:
            # Default response
            user_response = "1"

        print(f"\nUser responds: {user_response}")

        # Send response
        try:
            session_data = await client.send_response(session_id, user_response)
            current_step += 1
            print_message(current_step, session_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                print(f"\nEnd of flow: {e.response.json()['detail']}")
                break
            raise

    # Show final session status
    print(f"\n{'='*80}")
    print("FINAL SESSION STATUS")
    print(f"{'='*80}")

    status = await client.get_session_status(session_id)
    print(f"\nSession ID: {status['session_id']}")
    print(f"Project ID: {status['project_id']}")
    print(f"Current Node: {status['current_node_id']}")
    print(f"Language: {status['language']}")
    print(f"Created: {status['created_at']}")

    # Clean up
    print(f"\n{'='*80}")
    print("CLEANING UP")
    print(f"{'='*80}")

    result = await client.end_session(session_id)
    print(f"\nSession {result['session_id']} deleted")

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
    print(f"\nTotal steps executed: {current_step}")
    print("\nMobile app integration notes:")
    print(f"   1. Store session_id for the duration of the protocol")
    print(f"   2. Display message_text to the user")
    print(f"   3. Show quick_replies as buttons/options when available")
    print(f"   4. Send user's selection to /protocol/respond")
    print(f"   5. Handle media_url by displaying images/videos")
    print(f"   6. Use next_scheduled_at to schedule notifications")
    print(f"   7. Check is_terminal to know when protocol is complete")


async def test_immediate_quit_flow():
    """Test the immediate quit ('iquit0') shortcut."""
    client = ProtocolAPIClient(API_BASE_URL, API_KEY)

    print(f"\n{'#'*80}")
    print("# Testing 'iquit0' Immediate Quit Flow")
    print(f"{'#'*80}")

    session_data = await client.start_session(
        project_id=PROJECT_ID,
        language="en",
        initial_response="iquit0"  # Shortcut for immediate quit
    )

    print_message(1, session_data)

    await client.end_session(session_data["session_id"])
    print("\n'iquit0' shortcut test complete")


async def test_spanish_language():
    """Test Spanish language version."""
    client = ProtocolAPIClient(API_BASE_URL, API_KEY)

    print(f"\n{'#'*80}")
    print("# Testing Spanish Language Protocol")
    print(f"{'#'*80}")

    session_data = await client.start_session(
        project_id=PROJECT_ID,
        language="es"  # Spanish
    )

    print_message(1, session_data)

    await client.end_session(session_data["session_id"])
    print("\nSpanish language test complete")


async def main():
    """Run all tests."""
    try:
        # Test 1: Full protocol flow
        await test_protocol_flow()

        # Test 2: Immediate quit shortcut
        await test_immediate_quit_flow()

        # Test 3: Spanish language
        await test_spanish_language()

        print(f"\n{'#'*80}")
        print("# ALL TESTS PASSED")
        print(f"{'#'*80}")

    except httpx.HTTPStatusError as e:
        print(f"\nHTTP Error: {e.response.status_code}")
        print(f"   {e.response.json()}")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
