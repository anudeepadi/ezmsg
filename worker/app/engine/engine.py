"""Scheduler engine for processing and sending messages."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


# ── Status constants ────────────────────────────────────────────────────────


class MessageStatus:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ABORTED = "ABORTED"


# ── Channel adapters ───────────────────────────────────────────────────────


async def _send_twilio_sms(phone_number: str, message_text: str) -> dict:
    """Send an SMS via Twilio REST API.

    Returns a dict with the Twilio message SID for status tracking.
    """
    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    message = client.messages.create(
        body=message_text,
        from_=settings.twilio_phone_number,
        to=phone_number,
    )
    logger.info("Twilio SMS sent: SID=%s to=%s", message.sid, phone_number)
    return {"sid": message.sid, "status": message.status}


async def _send_fcm_push(
    fcm_token: str,
    message_text: str,
    node_id: int | None = None,
    quick_replies: list | None = None,
) -> dict:
    """Send a push notification via Firebase Cloud Messaging."""
    import firebase_admin
    from firebase_admin import messaging

    # Initialize Firebase app if not already done
    if not firebase_admin._apps:
        if settings.firebase_credentials_json:
            import json as _json
            cred_dict = _json.loads(settings.firebase_credentials_json)
            cred = firebase_admin.credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif settings.fcm_credentials_path:
            cred = firebase_admin.credentials.Certificate(settings.fcm_credentials_path)
            firebase_admin.initialize_app(cred)
        else:
            raise RuntimeError("No Firebase credentials configured")

    data_payload = {}
    if node_id is not None:
        data_payload["node_id"] = str(node_id)
    if quick_replies:
        data_payload["quick_replies"] = json.dumps(quick_replies)

    message = messaging.Message(
        notification=messaging.Notification(
            title="QuitTxt",
            body=message_text,
        ),
        data=data_payload if data_payload else None,
        token=fcm_token,
    )
    response = messaging.send(message)
    logger.info("FCM push sent: response=%s", response)
    return {"message_id": response}


# ── Main engine ─────────────────────────────────────────────────────────────


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
        logger.info("Starting scheduler engine: %s", self.worker_id)
        self.running = True

        while self.running:
            try:
                processed = await self._poll_iteration()
                if processed == 0:
                    await asyncio.sleep(settings.poll_interval_seconds)
                else:
                    logger.info("Processed %d messages", processed)
            except Exception as e:
                logger.error("Error in poll iteration: %s", e, exc_info=True)
                await asyncio.sleep(settings.poll_interval_seconds)

    async def stop(self):
        """Stop the scheduler engine."""
        logger.info("Stopping scheduler engine")
        self.running = False

    async def _poll_iteration(self) -> int:
        """Run a single poll iteration. Returns number of messages processed."""
        async with self.session_factory() as session:
            messages = await self._claim_messages(session)
            if not messages:
                return 0

            processed = 0
            for message in messages:
                try:
                    await self._process_message(session, message)
                    processed += 1
                except Exception as e:
                    logger.error("Error processing message %s: %s", message["id"], e, exc_info=True)
                    await self._handle_failure(session, message, str(e))

            await session.commit()
            return processed

    async def _claim_messages(self, session: AsyncSession) -> List[dict]:
        """Claim pending messages using FOR UPDATE SKIP LOCKED."""
        now = datetime.now(timezone.utc)

        query = text("""
            UPDATE scheduled_messages
            SET status = :in_progress,
                locked_by = :worker_id,
                locked_at = :now,
                updated_at = :now
            WHERE id IN (
                SELECT id FROM scheduled_messages
                WHERE status = :pending
                  AND send_at <= :now
                  AND (last_attempt_at IS NULL
                       OR last_attempt_at + make_interval(secs =>
                           LEAST(POWER(2, attempt_count) * :initial_delay, :max_delay)
                       ) <= :now)
                ORDER BY send_at
                LIMIT :batch_size
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, participant_id, project_id, messaging_node_id,
                      template_id, attempt_count, send_at, channel_type,
                      message_body, media_url, quick_replies
        """)

        result = await session.execute(
            query,
            {
                "in_progress": MessageStatus.IN_PROGRESS,
                "worker_id": self.worker_id,
                "now": now,
                "pending": MessageStatus.PENDING,
                "batch_size": settings.batch_size,
                "initial_delay": settings.initial_retry_delay_seconds,
                "max_delay": settings.max_retry_delay_seconds,
            },
        )

        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def _process_message(self, session: AsyncSession, message: dict):
        """Process a single claimed message.

        1. Load participant + resolve template
        2. Substitute variables
        3. Send via appropriate channel
        4. Mark as sent
        5. Schedule dependent nodes (evaluate conditions)
        6. Check terminal node
        """
        message_id = message["id"]
        participant_id = message["participant_id"]
        node_id = message.get("messaging_node_id")
        channel_type = message.get("channel_type", "MOBILE_APP")

        logger.info("Processing message %d for participant %d", message_id, participant_id)

        # Load participant
        participant = await self._get_participant(session, participant_id)
        if not participant:
            raise RuntimeError(f"Participant {participant_id} not found")

        # Resolve message text
        message_text = message.get("message_body") or ""
        if not message_text and node_id:
            message_text = await self._resolve_template(
                session, node_id, participant["current_language_id"]
            )

        if not message_text:
            logger.warning("No message text for message %d, skipping", message_id)
            await self._mark_status(session, message_id, MessageStatus.SKIPPED)
            return

        # Variable substitution
        message_text = await self._substitute_variables(
            session, message_text, participant_id
        )

        # Send via channel
        external_id = None
        if settings.simulation_mode:
            await self._send_simulation(participant, message_text)
        elif channel_type == "TWILIO":
            if not participant.get("phone_number"):
                raise RuntimeError("Participant has no phone number for Twilio")
            result = await _send_twilio_sms(participant["phone_number"], message_text)
            external_id = result.get("sid")
        elif channel_type == "MOBILE_APP":
            if not participant.get("fcm_token"):
                raise RuntimeError("Participant has no FCM token")
            await _send_fcm_push(
                participant["fcm_token"],
                message_text,
                node_id=node_id,
                quick_replies=message.get("quick_replies"),
            )
        else:
            logger.warning("Unknown channel %s, using simulation", channel_type)
            await self._send_simulation(participant, message_text)

        # Mark as sent
        now = datetime.now(timezone.utc)
        await session.execute(
            text("""
                UPDATE scheduled_messages
                SET status = :sent, sent_at = :now, updated_at = :now,
                    external_id = COALESCE(:external_id, external_id)
                WHERE id = :message_id
            """),
            {
                "sent": MessageStatus.SENT,
                "now": now,
                "message_id": message_id,
                "external_id": external_id,
            },
        )

        # Schedule dependent nodes
        if node_id:
            await self._schedule_dependent_nodes(session, participant, node_id)
            await self._check_terminal_node(session, participant_id, node_id)

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _get_participant(self, session: AsyncSession, participant_id: int) -> dict | None:
        result = await session.execute(
            text("""
                SELECT p.id, p.uu_id, p.project_id, p.channel_type,
                       p.current_language_id, p.phone_number, p.fcm_token,
                       p.timezone, p.status, p.metadata as extra_data
                FROM participants p
                WHERE p.id = :pid AND p.removed_at IS NULL
            """),
            {"pid": participant_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def _resolve_template(
        self, session: AsyncSession, node_id: int, language_id: int,
    ) -> str:
        result = await session.execute(
            text("""
                SELECT mtt.message_text
                FROM message_template_texts mtt
                JOIN message_templates mt ON mtt.template_id = mt.id
                JOIN messaging_nodes mn ON mn.template_id = mt.id
                WHERE mn.id = :node_id AND mtt.language_id = :lang_id
            """),
            {"node_id": node_id, "lang_id": language_id},
        )
        row = result.fetchone()
        if row:
            return row.message_text or ""
        # Fallback to English
        result = await session.execute(
            text("""
                SELECT mtt.message_text
                FROM message_template_texts mtt
                JOIN message_templates mt ON mtt.template_id = mt.id
                JOIN messaging_nodes mn ON mn.template_id = mt.id
                WHERE mn.id = :node_id AND mtt.language_id = 1
            """),
            {"node_id": node_id},
        )
        row = result.fetchone()
        return row.message_text if row else ""

    async def _substitute_variables(
        self, session: AsyncSession, text_str: str, participant_id: int,
    ) -> str:
        if "{{" not in text_str:
            return text_str

        result = await session.execute(
            text("""
                SELECT v.name, COALESCE(pvv.variable_value, v.default_value) as value
                FROM variables v
                LEFT JOIN participant_variable_values pvv
                    ON v.id = pvv.variable_id AND pvv.participant_id = :pid
                JOIN participants p ON v.project_id = p.project_id
                WHERE p.id = :pid
            """),
            {"pid": participant_id},
        )
        variables = {row.name: row.value or "" for row in result.fetchall()}

        for name, value in variables.items():
            text_str = text_str.replace(f"{{{{{name}}}}}", str(value))

        return text_str

    async def _send_simulation(self, participant: dict, message_text: str):
        logger.info(
            "[SIMULATION] -> participant %s (%s): %s",
            participant["id"],
            participant.get("channel_type", "?"),
            message_text[:120],
        )

    async def _get_participant_variables(
        self, session: AsyncSession, participant_id: int,
    ) -> dict[str, Any]:
        """Load all variable values for a participant as a dict."""
        result = await session.execute(
            text("""
                SELECT v.name, COALESCE(pvv.variable_value, v.default_value) as value
                FROM variables v
                LEFT JOIN participant_variable_values pvv
                    ON v.id = pvv.variable_id AND pvv.participant_id = :pid
                JOIN participants p ON v.project_id = p.project_id
                WHERE p.id = :pid
            """),
            {"pid": participant_id},
        )
        return {row.name: row.value for row in result.fetchall()}

    async def _evaluate_edge_condition(
        self, session: AsyncSession, condition_expression_id: int, participant_id: int,
    ) -> bool:
        """Evaluate a conditional expression for an edge."""
        # Load the condition text
        result = await session.execute(
            text("SELECT condition_text FROM conditional_expressions WHERE id = :cid"),
            {"cid": condition_expression_id},
        )
        row = result.fetchone()
        if not row or not row.condition_text:
            return True  # No condition = always true

        variables = await self._get_participant_variables(session, participant_id)

        # Use the safe evaluator (local copy in worker)
        from app.engine.condition_eval import evaluate_condition
        return evaluate_condition(row.condition_text, variables)

    def _participant_local_time(
        self, participant: dict, at_hour: int, at_minute: int = 0,
        base_date: datetime | None = None,
    ) -> datetime:
        """Calculate a UTC datetime for a specific local time in participant's timezone."""
        tz_name = participant.get("timezone") or "America/Chicago"
        try:
            tz = ZoneInfo(tz_name)
        except (KeyError, ValueError):
            tz = ZoneInfo("America/Chicago")

        base = base_date or datetime.now(timezone.utc)
        local_now = base.astimezone(tz)
        local_target = local_now.replace(
            hour=at_hour, minute=at_minute, second=0, microsecond=0
        )
        # If the target time has already passed today, schedule for tomorrow
        if local_target <= local_now:
            local_target += timedelta(days=1)
        return local_target.astimezone(timezone.utc)

    async def _schedule_dependent_nodes(
        self, session: AsyncSession, participant: dict, current_node_id: int,
    ):
        """Schedule messages for dependent nodes (outgoing edges).

        Evaluates conditional expressions on edges and only schedules
        children whose conditions are met.
        """
        participant_id = participant["id"]
        tz_name = participant.get("timezone") or "America/Chicago"
        try:
            tz = ZoneInfo(tz_name)
        except (KeyError, ValueError):
            tz = ZoneInfo("America/Chicago")

        # Get outgoing edges with timing info
        edge_result = await session.execute(
            text("""
                SELECT mne.child_node_id, mne.condition_expression_id,
                       mne.edge_label, mne.edge_order,
                       mn.timing_element_id, mn.template_id, mn.project_id,
                       mn.is_terminal_node, mn.exec_commands,
                       mn.metadata as node_extra
                FROM messaging_node_edges mne
                JOIN messaging_nodes mn ON mne.child_node_id = mn.id
                WHERE mne.parent_node_id = :node_id
                  AND mne.removed_at IS NULL
                  AND mn.removed_at IS NULL
                ORDER BY mne.edge_order
            """),
            {"node_id": current_node_id},
        )
        edges = edge_result.fetchall()

        now = datetime.now(timezone.utc)

        for edge in edges:
            # Evaluate condition if present
            if edge.condition_expression_id:
                try:
                    passes = await self._evaluate_edge_condition(
                        session, edge.condition_expression_id, participant_id,
                    )
                    if not passes:
                        logger.debug(
                            "Condition %d not met for participant %d, skipping edge to node %d",
                            edge.condition_expression_id, participant_id, edge.child_node_id,
                        )
                        continue
                except Exception as e:
                    logger.error("Error evaluating condition %d: %s", edge.condition_expression_id, e)
                    continue

            # Calculate scheduled time using timing element (timezone-aware)
            send_at = now
            if edge.timing_element_id:
                timing_result = await session.execute(
                    text("""
                        SELECT offset_days, offset_hours, offset_minutes, offset_seconds,
                               overwrite_time, overwritten_hours, overwritten_minutes
                        FROM timing_elements WHERE id = :tid
                    """),
                    {"tid": edge.timing_element_id},
                )
                timing = timing_result.fetchone()
                if timing:
                    offset = timedelta(
                        days=timing.offset_days or 0,
                        hours=timing.offset_hours or 0,
                        minutes=timing.offset_minutes or 0,
                        seconds=timing.offset_seconds or 0,
                    )
                    send_at = now + offset

                    # Apply overwritten time in participant's local timezone
                    if timing.overwrite_time and timing.overwritten_hours is not None:
                        local_time = send_at.astimezone(tz)
                        local_time = local_time.replace(
                            hour=timing.overwritten_hours,
                            minute=timing.overwritten_minutes or 0,
                            second=0, microsecond=0,
                        )
                        send_at = local_time.astimezone(timezone.utc)

            # Determine channel type from participant
            channel_type = participant.get("channel_type", "MOBILE_APP")

            await session.execute(
                text("""
                    INSERT INTO scheduled_messages
                        (participant_id, project_id, messaging_node_id, template_id,
                         status, send_at, channel_type, created_at, updated_at)
                    VALUES
                        (:pid, :project_id, :node_id, :template_id,
                         :status, :send_at, :channel_type, :now, :now)
                """),
                {
                    "pid": participant_id,
                    "project_id": edge.project_id,
                    "node_id": edge.child_node_id,
                    "template_id": edge.template_id,
                    "status": MessageStatus.PENDING,
                    "send_at": send_at,
                    "channel_type": channel_type,
                    "now": now,
                },
            )

            logger.info(
                "Scheduled node %d for participant %d at %s",
                edge.child_node_id, participant_id, send_at,
            )

    async def _check_terminal_node(
        self, session: AsyncSession, participant_id: int, node_id: int,
    ):
        """Check if node is terminal and handle participant completion."""
        result = await session.execute(
            text("SELECT is_terminal_node FROM messaging_nodes WHERE id = :nid"),
            {"nid": node_id},
        )
        node = result.fetchone()

        if node and node.is_terminal_node:
            logger.info("Participant %d reached terminal node %d", participant_id, node_id)
            now = datetime.now(timezone.utc)

            await session.execute(
                text("""
                    UPDATE participants
                    SET status = 'COMPLETED', completed_at = :now, updated_at = :now
                    WHERE id = :pid
                """),
                {"now": now, "pid": participant_id},
            )

            await session.execute(
                text("""
                    UPDATE scheduled_messages
                    SET status = :aborted, updated_at = :now
                    WHERE participant_id = :pid AND status = :pending
                """),
                {
                    "aborted": MessageStatus.ABORTED,
                    "now": now,
                    "pid": participant_id,
                    "pending": MessageStatus.PENDING,
                },
            )

    async def _handle_failure(
        self, session: AsyncSession, message: dict, error: str,
    ):
        """Handle message processing failure with exponential backoff."""
        message_id = message["id"]
        attempt_count = message.get("attempt_count", 0) + 1
        now = datetime.now(timezone.utc)

        if attempt_count >= settings.max_retries:
            await session.execute(
                text("""
                    UPDATE scheduled_messages
                    SET status = :failed,
                        last_error_message = :error,
                        attempt_count = :attempts,
                        updated_at = :now
                    WHERE id = :mid
                """),
                {
                    "failed": MessageStatus.FAILED,
                    "error": error[:500],
                    "attempts": attempt_count,
                    "now": now,
                    "mid": message_id,
                },
            )
            logger.error(
                "Message %d permanently failed after %d attempts", message_id, attempt_count,
            )
        else:
            delay = min(
                settings.initial_retry_delay_seconds * (2 ** (attempt_count - 1)),
                settings.max_retry_delay_seconds,
            )
            next_retry = now + timedelta(seconds=delay)

            await session.execute(
                text("""
                    UPDATE scheduled_messages
                    SET status = :pending,
                        last_error_message = :error,
                        attempt_count = :attempts,
                        last_attempt_at = :now,
                        locked_by = NULL,
                        locked_at = NULL,
                        updated_at = :now
                    WHERE id = :mid
                """),
                {
                    "pending": MessageStatus.PENDING,
                    "error": error[:500],
                    "attempts": attempt_count,
                    "now": now,
                    "mid": message_id,
                },
            )
            logger.warning(
                "Message %d failed (attempt %d), retry after %ds",
                message_id, attempt_count, delay,
            )

    async def _mark_status(self, session: AsyncSession, message_id: int, status: str):
        now = datetime.now(timezone.utc)
        await session.execute(
            text("""
                UPDATE scheduled_messages SET status = :s, updated_at = :now WHERE id = :mid
            """),
            {"s": status, "now": now, "mid": message_id},
        )

    # ── V11-specific scheduling methods ─────────────────────────────────

    async def schedule_intermittent_messages(
        self, session: AsyncSession, participant: dict,
        project_id: int, quit_day_date: datetime,
        template_ids: list[int],
    ) -> int:
        """Schedule intermittent messages at 1pm/4pm/7pm participant local time.

        Called when a participant enters a new quit day. Creates 3 scheduled
        messages for that day.
        """
        hours = [13, 16, 19]  # 1pm, 4pm, 7pm
        now = datetime.now(timezone.utc)
        count = 0

        for i, hour in enumerate(hours):
            template_id = template_ids[i] if i < len(template_ids) else template_ids[-1]
            send_at = self._participant_local_time(participant, hour, base_date=quit_day_date)

            await session.execute(
                text("""
                    INSERT INTO scheduled_messages
                        (participant_id, project_id, template_id,
                         status, send_at, channel_type, created_at, updated_at,
                         metadata)
                    VALUES
                        (:pid, :project_id, :template_id,
                         :status, :send_at, :channel_type, :now, :now,
                         :meta)
                """),
                {
                    "pid": participant["id"],
                    "project_id": project_id,
                    "template_id": template_id,
                    "status": MessageStatus.PENDING,
                    "send_at": send_at,
                    "channel_type": participant.get("channel_type", "MOBILE_APP"),
                    "now": now,
                    "meta": json.dumps({"type": "intermittent", "hour": hour}),
                },
            )
            count += 1

        logger.info(
            "Scheduled %d intermittent messages for participant %d on %s",
            count, participant["id"], quit_day_date.date(),
        )
        return count

    async def schedule_checkout(
        self, session: AsyncSession, participant: dict,
        project_id: int, checkout_node_id: int,
        checkout_date: datetime,
    ) -> None:
        """Schedule an 8pm checkout message for a quit day."""
        send_at = self._participant_local_time(participant, 20, base_date=checkout_date)
        now = datetime.now(timezone.utc)

        await session.execute(
            text("""
                INSERT INTO scheduled_messages
                    (participant_id, project_id, messaging_node_id,
                     status, send_at, channel_type, created_at, updated_at,
                     metadata)
                VALUES
                    (:pid, :project_id, :node_id,
                     :status, :send_at, :channel_type, :now, :now,
                     :meta)
            """),
            {
                "pid": participant["id"],
                "project_id": project_id,
                "node_id": checkout_node_id,
                "status": MessageStatus.PENDING,
                "send_at": send_at,
                "channel_type": participant.get("channel_type", "MOBILE_APP"),
                "now": now,
                "meta": json.dumps({"type": "checkout"}),
            },
        )

        logger.info(
            "Scheduled 8pm checkout for participant %d on %s",
            participant["id"], checkout_date.date(),
        )

    async def schedule_pre_quit_messages(
        self, session: AsyncSession, participant: dict,
        project_id: int, quit_date: datetime, pre_quit_node_ids: list[dict],
    ) -> int:
        """Schedule pre-quit messages from PQ-6 to PQ-1 based on quit date.

        Called when a participant sets their quit date during intake.

        Args:
            participant: dict with id, timezone, channel_type
            project_id: project ID
            quit_date: the participant's quit date (UTC)
            pre_quit_node_ids: list of dicts with {day_offset, morning_node_id, afternoon_node_id}
                where day_offset is negative (e.g., -6 for PQ-6, -1 for PQ-1).
                morning_node_id sends at 8am local, afternoon_node_id at 1pm local.

        Returns:
            Number of messages scheduled.
        """
        now = datetime.now(timezone.utc)
        count = 0

        for pq_day in pre_quit_node_ids:
            day_offset = pq_day["day_offset"]
            msg_date = quit_date + timedelta(days=day_offset)

            # Skip if this date has already passed
            if msg_date.date() < now.astimezone(
                ZoneInfo(participant.get("timezone") or "America/Chicago")
            ).date():
                logger.info(
                    "Skipping PQ day %d (already past) for participant %d",
                    day_offset, participant["id"],
                )
                continue

            # Morning message at 8am local
            if pq_day.get("morning_node_id"):
                send_at = self._participant_local_time(
                    participant, 8, base_date=msg_date,
                )
                await session.execute(
                    text("""
                        INSERT INTO scheduled_messages
                            (participant_id, project_id, messaging_node_id,
                             status, send_at, channel_type, created_at, updated_at,
                             metadata)
                        VALUES
                            (:pid, :project_id, :node_id,
                             :status, :send_at, :channel_type, :now, :now,
                             :meta)
                    """),
                    {
                        "pid": participant["id"],
                        "project_id": project_id,
                        "node_id": pq_day["morning_node_id"],
                        "status": MessageStatus.PENDING,
                        "send_at": send_at,
                        "channel_type": participant.get("channel_type", "MOBILE_APP"),
                        "now": now,
                        "meta": json.dumps({
                            "type": "pre_quit",
                            "pq_day": day_offset,
                            "slot": "morning",
                        }),
                    },
                )
                count += 1

            # Afternoon message at 1pm local
            if pq_day.get("afternoon_node_id"):
                send_at = self._participant_local_time(
                    participant, 13, base_date=msg_date,
                )
                await session.execute(
                    text("""
                        INSERT INTO scheduled_messages
                            (participant_id, project_id, messaging_node_id,
                             status, send_at, channel_type, created_at, updated_at,
                             metadata)
                        VALUES
                            (:pid, :project_id, :node_id,
                             :status, :send_at, :channel_type, :now, :now,
                             :meta)
                    """),
                    {
                        "pid": participant["id"],
                        "project_id": project_id,
                        "node_id": pq_day["afternoon_node_id"],
                        "status": MessageStatus.PENDING,
                        "send_at": send_at,
                        "channel_type": participant.get("channel_type", "MOBILE_APP"),
                        "now": now,
                        "meta": json.dumps({
                            "type": "pre_quit",
                            "pq_day": day_offset,
                            "slot": "afternoon",
                        }),
                    },
                )
                count += 1

        logger.info(
            "Scheduled %d pre-quit messages for participant %d (quit date: %s)",
            count, participant["id"], quit_date.date(),
        )
        return count

    async def schedule_quit_day(
        self, session: AsyncSession, participant: dict,
        project_id: int, quit_day_num: int, day_date: datetime,
        morning_node_id: int, intermittent_template_ids: list[int],
        checkout_node_id: int,
    ) -> int:
        """Schedule all messages for a single quit day.

        Creates: morning session + 3 intermittent messages (1pm/4pm/7pm) + 8pm checkout.

        Returns:
            Number of messages scheduled.
        """
        now = datetime.now(timezone.utc)
        count = 0

        # Morning session at 8am local
        send_at = self._participant_local_time(participant, 8, base_date=day_date)
        await session.execute(
            text("""
                INSERT INTO scheduled_messages
                    (participant_id, project_id, messaging_node_id,
                     status, send_at, channel_type, created_at, updated_at,
                     metadata)
                VALUES
                    (:pid, :project_id, :node_id,
                     :status, :send_at, :channel_type, :now, :now,
                     :meta)
            """),
            {
                "pid": participant["id"],
                "project_id": project_id,
                "node_id": morning_node_id,
                "status": MessageStatus.PENDING,
                "send_at": send_at,
                "channel_type": participant.get("channel_type", "MOBILE_APP"),
                "now": now,
                "meta": json.dumps({
                    "type": "morning_session",
                    "quit_day": quit_day_num,
                }),
            },
        )
        count += 1

        # Intermittent messages at 1pm/4pm/7pm
        count += await self.schedule_intermittent_messages(
            session, participant, project_id, day_date, intermittent_template_ids,
        )

        # Checkout at 8pm
        await self.schedule_checkout(
            session, participant, project_id, checkout_node_id, day_date,
        )
        count += 1

        logger.info(
            "Scheduled quit day Q%d (%d messages) for participant %d on %s",
            quit_day_num, count, participant["id"], day_date.date(),
        )
        return count
