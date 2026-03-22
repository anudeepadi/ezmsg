"""Scheduler engine for processing messages."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


# Status constants
class MessageStatus:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ABORTED = "ABORTED"


class SchedulerEngine:
    """Main scheduler engine for processing messages."""

    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )
        self.running = False
        self.worker_id = f"worker-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    async def start(self):
        """Start the scheduler engine."""
        logger.info(f"Starting scheduler engine: {self.worker_id}")
        self.running = True

        while self.running:
            try:
                processed = await self._poll_iteration()
                if processed == 0:
                    # No messages to process, wait before polling again
                    await asyncio.sleep(settings.poll_interval_seconds)
                else:
                    logger.info(f"Processed {processed} messages")
            except Exception as e:
                logger.error(f"Error in poll iteration: {e}")
                await asyncio.sleep(settings.poll_interval_seconds)

    async def stop(self):
        """Stop the scheduler engine."""
        logger.info("Stopping scheduler engine")
        self.running = False

    async def _poll_iteration(self) -> int:
        """Run a single poll iteration.

        Returns:
            Number of messages processed
        """
        async with self.session_factory() as session:
            # Claim messages using FOR UPDATE SKIP LOCKED
            messages = await self._claim_messages(session)
            if not messages:
                return 0

            # Process each message
            processed = 0
            for message in messages:
                try:
                    await self._process_message(session, message)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {e}")
                    await self._handle_failure(session, message, str(e))

            await session.commit()
            return processed

    async def _claim_messages(self, session: AsyncSession) -> List[dict]:
        """Claim pending messages for processing.

        Uses FOR UPDATE SKIP LOCKED to prevent contention between workers.
        """
        now = datetime.now(timezone.utc)

        # Raw SQL for the claiming query with SKIP LOCKED
        query = """
            UPDATE scheduled_messages
            SET status = :in_progress,
                claimed_by = :worker_id,
                claimed_at = :now,
                updated_at = :now
            WHERE id IN (
                SELECT id FROM scheduled_messages
                WHERE status = :pending
                  AND scheduled_at <= :now
                  AND (next_retry_at IS NULL OR next_retry_at <= :now)
                ORDER BY scheduled_at
                LIMIT :batch_size
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, participant_id, project_id, node_id,
                      template_id, attempt_count, scheduled_at
        """

        result = await session.execute(
            query,
            {
                "in_progress": MessageStatus.IN_PROGRESS,
                "worker_id": self.worker_id,
                "now": now,
                "pending": MessageStatus.PENDING,
                "batch_size": settings.batch_size,
            },
        )

        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def _process_message(self, session: AsyncSession, message: dict):
        """Process a single message.

        1. Resolve template with variable substitution
        2. Send via channel adapter
        3. Mark as sent
        4. Schedule dependent nodes
        """
        message_id = message["id"]
        participant_id = message["participant_id"]
        node_id = message["node_id"]

        logger.info(f"Processing message {message_id} for participant {participant_id}")

        # Get participant info
        participant_query = """
            SELECT p.*, l.code as language_code
            FROM participants p
            LEFT JOIN languages l ON p.current_language_id = l.id
            WHERE p.id = :participant_id
        """
        participant_result = await session.execute(
            participant_query, {"participant_id": participant_id}
        )
        participant = participant_result.fetchone()

        if not participant:
            raise Exception(f"Participant {participant_id} not found")

        # Get template
        template_query = """
            SELECT mtt.message_text, mtt.media_url, mtt.media_type, mtt.quick_replies
            FROM message_template_texts mtt
            JOIN message_templates mt ON mtt.template_id = mt.id
            JOIN messaging_nodes mn ON mn.template_id = mt.id
            WHERE mn.id = :node_id
              AND mtt.language_id = :language_id
        """
        template_result = await session.execute(
            template_query,
            {
                "node_id": node_id,
                "language_id": participant.current_language_id,
            },
        )
        template = template_result.fetchone()

        if not template:
            # Try fallback to English (language_id = 1)
            template_result = await session.execute(
                template_query.replace(":language_id", "1"),
                {"node_id": node_id},
            )
            template = template_result.fetchone()

        if not template or not template.message_text:
            raise Exception(f"No template found for node {node_id}")

        # Resolve variables in message text
        message_text = await self._substitute_variables(
            session, template.message_text, participant_id
        )

        # Send the message
        if settings.simulation_mode:
            await self._send_simulation(participant, message_text)
        else:
            await self._send_fcm(participant, message_text, template.quick_replies)

        # Mark as sent
        now = datetime.now(timezone.utc)
        update_query = """
            UPDATE scheduled_messages
            SET status = :sent, sent_at = :now, updated_at = :now
            WHERE id = :message_id
        """
        await session.execute(
            update_query,
            {"sent": MessageStatus.SENT, "now": now, "message_id": message_id},
        )

        # Schedule dependent nodes
        await self._schedule_dependent_nodes(session, participant_id, node_id)

        # Check if this was a terminal node
        await self._check_terminal_node(session, participant_id, node_id)

    async def _substitute_variables(
        self, session: AsyncSession, text: str, participant_id: int
    ) -> str:
        """Substitute variables in message text."""
        if "{{" not in text:
            return text

        # Get participant variables
        query = """
            SELECT v.name, COALESCE(pvv.value, v.default_value) as value
            FROM variables v
            LEFT JOIN participant_variable_values pvv
                ON v.id = pvv.variable_id AND pvv.participant_id = :participant_id
            JOIN participants p ON v.project_id = p.project_id
            WHERE p.id = :participant_id
        """
        result = await session.execute(query, {"participant_id": participant_id})
        variables = {row.name: row.value or "" for row in result.fetchall()}

        # Simple substitution
        for name, value in variables.items():
            text = text.replace(f"{{{{{name}}}}}", str(value))

        return text

    async def _send_simulation(self, participant, message_text: str):
        """Send message in simulation mode (development)."""
        logger.info(
            f"[SIMULATION] Sending to participant {participant.id}: {message_text[:100]}..."
        )

    async def _send_fcm(
        self, participant, message_text: str, quick_replies: Optional[list]
    ):
        """Send message via FCM."""
        if not participant.fcm_token:
            raise Exception("Participant has no FCM token")

        # TODO: Implement actual FCM sending
        # import firebase_admin
        # from firebase_admin import messaging
        raise NotImplementedError("FCM sending not implemented")

    async def _schedule_dependent_nodes(
        self, session: AsyncSession, participant_id: int, current_node_id: int
    ):
        """Schedule messages for dependent nodes (outgoing edges)."""
        # Get outgoing edges
        edge_query = """
            SELECT mne.child_node_id, mn.timing_element_id
            FROM messaging_node_edges mne
            JOIN messaging_nodes mn ON mne.child_node_id = mn.id
            WHERE mne.parent_node_id = :node_id
              AND mne.removed_at IS NULL
              AND mn.removed_at IS NULL
        """
        edges_result = await session.execute(
            edge_query, {"node_id": current_node_id}
        )
        edges = edges_result.fetchall()

        now = datetime.now(timezone.utc)

        for edge in edges:
            child_node_id = edge.child_node_id
            timing_element_id = edge.timing_element_id

            # Calculate scheduled time based on timing element
            scheduled_at = now
            if timing_element_id:
                timing_query = """
                    SELECT offset_minutes FROM timing_elements WHERE id = :timing_id
                """
                timing_result = await session.execute(
                    timing_query, {"timing_id": timing_element_id}
                )
                timing = timing_result.fetchone()
                if timing:
                    scheduled_at = now + timedelta(minutes=timing.offset_minutes)

            # Get project_id and template_id for the child node
            node_query = """
                SELECT project_id, template_id FROM messaging_nodes WHERE id = :node_id
            """
            node_result = await session.execute(
                node_query, {"node_id": child_node_id}
            )
            node = node_result.fetchone()

            # Insert new scheduled message
            insert_query = """
                INSERT INTO scheduled_messages
                    (participant_id, project_id, node_id, template_id,
                     status, scheduled_at, created_at, updated_at)
                VALUES
                    (:participant_id, :project_id, :node_id, :template_id,
                     :status, :scheduled_at, :now, :now)
            """
            await session.execute(
                insert_query,
                {
                    "participant_id": participant_id,
                    "project_id": node.project_id,
                    "node_id": child_node_id,
                    "template_id": node.template_id,
                    "status": MessageStatus.PENDING,
                    "scheduled_at": scheduled_at,
                    "now": now,
                },
            )

            logger.info(
                f"Scheduled node {child_node_id} for participant {participant_id} at {scheduled_at}"
            )

    async def _check_terminal_node(
        self, session: AsyncSession, participant_id: int, node_id: int
    ):
        """Check if the node is terminal and handle completion."""
        # Check if node is terminal
        query = """
            SELECT is_terminal_node FROM messaging_nodes WHERE id = :node_id
        """
        result = await session.execute(query, {"node_id": node_id})
        node = result.fetchone()

        if node and node.is_terminal_node:
            logger.info(f"Participant {participant_id} reached terminal node {node_id}")

            # Update participant status to COMPLETED
            now = datetime.now(timezone.utc)
            update_participant = """
                UPDATE participants
                SET status = 'COMPLETED', completed_at = :now, updated_at = :now
                WHERE id = :participant_id
            """
            await session.execute(
                update_participant,
                {"now": now, "participant_id": participant_id},
            )

            # Abort any remaining pending messages
            abort_messages = """
                UPDATE scheduled_messages
                SET status = :aborted, updated_at = :now
                WHERE participant_id = :participant_id
                  AND status = :pending
            """
            await session.execute(
                abort_messages,
                {
                    "aborted": MessageStatus.ABORTED,
                    "now": now,
                    "participant_id": participant_id,
                    "pending": MessageStatus.PENDING,
                },
            )

    async def _handle_failure(
        self, session: AsyncSession, message: dict, error: str
    ):
        """Handle message processing failure with exponential backoff."""
        message_id = message["id"]
        attempt_count = message["attempt_count"] + 1

        now = datetime.now(timezone.utc)

        if attempt_count >= settings.max_retries:
            # Max retries exceeded, mark as failed
            update_query = """
                UPDATE scheduled_messages
                SET status = :failed,
                    error_message = :error,
                    attempt_count = :attempts,
                    updated_at = :now
                WHERE id = :message_id
            """
            await session.execute(
                update_query,
                {
                    "failed": MessageStatus.FAILED,
                    "error": error,
                    "attempts": attempt_count,
                    "now": now,
                    "message_id": message_id,
                },
            )
            logger.error(
                f"Message {message_id} permanently failed after {attempt_count} attempts"
            )
        else:
            # Calculate exponential backoff
            delay_seconds = min(
                settings.initial_retry_delay_seconds * (2 ** (attempt_count - 1)),
                settings.max_retry_delay_seconds,
            )
            next_retry = now + timedelta(seconds=delay_seconds)

            update_query = """
                UPDATE scheduled_messages
                SET status = :pending,
                    error_message = :error,
                    attempt_count = :attempts,
                    next_retry_at = :next_retry,
                    claimed_by = NULL,
                    claimed_at = NULL,
                    updated_at = :now
                WHERE id = :message_id
            """
            await session.execute(
                update_query,
                {
                    "pending": MessageStatus.PENDING,
                    "error": error,
                    "attempts": attempt_count,
                    "next_retry": next_retry,
                    "now": now,
                    "message_id": message_id,
                },
            )
            logger.warning(
                f"Message {message_id} failed (attempt {attempt_count}), retry at {next_retry}"
            )
