"""Public API for protocol interaction via API key."""

from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models import (
    Project, MessagingNode, MessagingNodeEdge,
    MessageTemplate, MessageTemplateText, TimingElement,
    Participant, ParticipantVariableValue,
)
from app.config import settings
from app.redis import save_session, get_session, delete_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Protocol API"])


class ProtocolStartRequest(BaseModel):
    """Request to start a protocol session."""
    project_id: int
    language: str = "en"  # "en" or "es"
    participant_uuid: str | None = None  # Link to enrolled participant
    timezone: str | None = None  # e.g., "America/Chicago"
    initial_response: str | None = None  # e.g., "iquit0" for immediate quit


class ProtocolResponseRequest(BaseModel):
    """Request to send a response in an ongoing session."""
    session_id: str
    response: str  # User's response (e.g., "1", "YES", "NO")


class ProtocolResumeRequest(BaseModel):
    """Request to resume a session for a participant."""
    participant_uuid: str
    language: str | None = None  # Override language (uses participant's if omitted)


class ProtocolMessage(BaseModel):
    """A message in the protocol."""
    message_text: Optional[str]
    media_url: Optional[str] = None
    quick_replies: list[dict[str, str]] = []
    expects_reply: bool = False
    is_terminal: bool = False


class ProtocolSessionResponse(BaseModel):
    """Response from starting or continuing a session."""
    session_id: str
    project_id: int
    project_name: str
    current_node_id: int
    current_node_name: str
    participant_uuid: str | None = None
    message: ProtocolMessage
    session_time: str
    next_scheduled_at: Optional[str] = None


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header."""
    if not settings.protocol_api_key:
        raise HTTPException(
            status_code=503,
            detail="Protocol API key not configured. Set PROTOCOL_API_KEY env var.",
        )
    if not secrets.compare_digest(x_api_key, settings.protocol_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


async def _get_protocol_context(project_id: int, db: AsyncSession) -> dict[str, Any]:
    """Load protocol data for a project."""
    # Get project
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get nodes
    nodes_result = await db.execute(
        select(MessagingNode)
        .where(MessagingNode.project_id == project_id)
        .order_by(MessagingNode.node_order)
    )
    nodes = nodes_result.scalars().all()
    nodes_map = {n.id: n for n in nodes}

    # Get edges
    node_ids = [n.id for n in nodes]
    edges_result = await db.execute(
        select(MessagingNodeEdge)
        .where(MessagingNodeEdge.parent_node_id.in_(node_ids))
        .order_by(MessagingNodeEdge.edge_order)
    )
    edges = edges_result.scalars().all()

    # Build adjacency list
    adjacency: dict[int, list[MessagingNodeEdge]] = {}
    for edge in edges:
        if edge.parent_node_id not in adjacency:
            adjacency[edge.parent_node_id] = []
        adjacency[edge.parent_node_id].append(edge)

    # Get templates with texts
    template_ids = [n.template_id for n in nodes if n.template_id]
    templates_map = {}
    if template_ids:
        templates_result = await db.execute(
            select(MessageTemplate)
            .options(selectinload(MessageTemplate.texts))
            .where(MessageTemplate.id.in_(template_ids))
        )
        templates = templates_result.scalars().all()
        templates_map = {t.id: t for t in templates}

    # Get timing elements
    timing_ids = [n.timing_element_id for n in nodes if n.timing_element_id]
    timings_map = {}
    if timing_ids:
        timing_result = await db.execute(
            select(TimingElement)
            .where(TimingElement.id.in_(timing_ids))
        )
        timings = timing_result.scalars().all()
        timings_map = {t.id: t for t in timings}

    return {
        "project": project,
        "nodes_map": nodes_map,
        "adjacency": adjacency,
        "templates_map": templates_map,
        "timings_map": timings_map,
    }


def _get_message_content(
    node: MessagingNode,
    language: str,
    templates_map: dict,
    adjacency: dict,
) -> tuple[Optional[str], Optional[str], list[dict], bool]:
    """Extract message content from a node."""
    if not node.template_id or node.template_id not in templates_map:
        return None, None, [], False

    template = templates_map[node.template_id]

    # Map language code to language_id
    language_id = 1 if language == "en" else 2  # 1=English, 2=Spanish

    # Find text for language
    text_obj = None
    for t in template.texts:
        if t.language_id == language_id:
            text_obj = t
            break

    # Fallback to first text
    if not text_obj and template.texts:
        text_obj = template.texts[0]

    if not text_obj:
        return None, None, [], False

    # Parse quick replies
    quick_replies = []
    if text_obj.quick_replies and isinstance(text_obj.quick_replies, list):
        for qr in text_obj.quick_replies:
            if isinstance(qr, dict) and "label" in qr and "value" in qr:
                quick_replies.append(qr)

    # Check if reply is expected
    edges = adjacency.get(node.id, [])
    has_labeled_edges = any(e.edge_label for e in edges)
    expects_reply = bool(quick_replies) or has_labeled_edges

    return text_obj.message_text, text_obj.media_url, quick_replies, expects_reply


def _calculate_next_time(
    timing_element_id: Optional[int],
    timings_map: dict,
    current_time: datetime
) -> datetime:
    """Calculate the next message time based on timing element."""
    if not timing_element_id or timing_element_id not in timings_map:
        return current_time

    timing = timings_map[timing_element_id]

    # Calculate offset
    offset = timedelta(
        days=timing.offset_days,
        hours=timing.offset_hours,
        minutes=timing.offset_minutes,
        seconds=timing.offset_seconds
    )

    scheduled_time = current_time + offset

    # Apply overwritten time if specified
    if timing.overwrite_time and timing.overwritten_hours is not None:
        scheduled_time = scheduled_time.replace(
            hour=timing.overwritten_hours,
            minute=timing.overwritten_minutes or 0,
            second=0,
            microsecond=0
        )

    return scheduled_time


@router.post("/protocol/start", response_model=ProtocolSessionResponse)
async def start_protocol_session(
    request: ProtocolStartRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> ProtocolSessionResponse:
    """
    Start a new protocol session.

    Use this endpoint to begin a protocol flow. You can provide an initial_response
    like "iquit0" to automatically progress through the entry node.

    Example:
        POST /v1/protocol/start
        Headers: X-API-Key: YOUR_PROTOCOL_API_KEY
        Body: {
            "project_id": 7,
            "language": "en",
            "initial_response": "iquit0"
        }
    """
    ctx = await _get_protocol_context(request.project_id, db)

    # Find entry node
    entry_node = None
    for node in ctx["nodes_map"].values():
        if node.is_entry_node:
            entry_node = node
            break

    if not entry_node:
        raise HTTPException(status_code=400, detail="No entry node found in protocol")

    # Resolve participant if participant_uuid provided
    participant: Participant | None = None
    if request.participant_uuid:
        result = await db.execute(
            select(Participant).where(
                Participant.uu_id == request.participant_uuid,
                Participant.project_id == request.project_id,
            )
        )
        participant = result.scalar_one_or_none()
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found in project")

        # Save timezone to participant if provided
        if request.timezone:
            extra = dict(participant.extra_data or {})
            extra["timezone"] = request.timezone
            participant.extra_data = extra
            await db.flush()

    # Create session
    session_id = str(uuid4())
    current_time = datetime.now(timezone.utc)

    # Start at entry node
    current_node = entry_node

    # If initial_response provided (like "iquit0"), auto-advance
    if request.initial_response:
        # Get edges from entry node
        edges = ctx["adjacency"].get(current_node.id, [])

        # Map common shortcuts
        response_upper = request.initial_response.upper()
        if response_upper == "IQUIT0":
            # This means "I want to quit now" -> look for YES_TOMORROW or immediate quit edge
            target_labels = ["YES_TOMORROW", "YES", "1"]
        else:
            target_labels = [response_upper]

        # Find matching edge
        next_edge = None
        for edge in edges:
            if edge.edge_label and edge.edge_label.upper() in target_labels:
                next_edge = edge
                break

        # Use default edge if no match
        if not next_edge and edges:
            next_edge = edges[0]

        # Advance to next node
        if next_edge:
            next_node_id = next_edge.child_node_id
            if next_node_id in ctx["nodes_map"]:
                current_node = ctx["nodes_map"][next_node_id]
                current_time = _calculate_next_time(
                    current_node.timing_element_id,
                    ctx["timings_map"],
                    current_time
                )

    # Get message content
    message_text, media_url, quick_replies, expects_reply = _get_message_content(
        current_node,
        request.language,
        ctx["templates_map"],
        ctx["adjacency"]
    )

    # Calculate next scheduled time
    next_scheduled = _calculate_next_time(
        current_node.timing_element_id,
        ctx["timings_map"],
        current_time
    )

    # Build session data for Redis
    session_data: dict[str, Any] = {
        "project_id": request.project_id,
        "language": request.language,
        "current_node_id": current_node.id,
        "current_time": current_time.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if participant:
        session_data["participant_id"] = participant.id
        session_data["participant_uuid"] = participant.uu_id

        # Persist current_node_id to participant for session recovery
        extra = dict(participant.extra_data or {})
        extra["current_node_id"] = current_node.id
        extra["session_id"] = session_id
        participant.extra_data = extra
        await db.flush()

    await save_session(session_id, session_data)

    return ProtocolSessionResponse(
        session_id=session_id,
        project_id=request.project_id,
        project_name=ctx["project"].name,
        current_node_id=current_node.id,
        current_node_name=current_node.name,
        participant_uuid=participant.uu_id if participant else None,
        message=ProtocolMessage(
            message_text=message_text,
            media_url=media_url,
            quick_replies=quick_replies,
            expects_reply=expects_reply,
            is_terminal=current_node.is_terminal_node,
        ),
        session_time=current_time.isoformat(),
        next_scheduled_at=next_scheduled.isoformat() if next_scheduled != current_time else None,
    )


@router.post("/protocol/respond", response_model=ProtocolSessionResponse)
async def respond_to_protocol(
    request: ProtocolResponseRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> ProtocolSessionResponse:
    """
    Send a response to continue the protocol flow.

    After receiving a message with expects_reply=true, use this endpoint
    to send your response and receive the next message.

    Example:
        POST /v1/protocol/respond
        Headers: X-API-Key: YOUR_PROTOCOL_API_KEY
        Body: {
            "session_id": "uuid-here",
            "response": "1"
        }
    """
    # Get session from Redis
    session = await get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    ctx = await _get_protocol_context(session["project_id"], db)

    # Get current node
    current_node = ctx["nodes_map"].get(session["current_node_id"])
    if not current_node:
        raise HTTPException(status_code=404, detail="Current node not found")

    # Get edges
    edges = ctx["adjacency"].get(current_node.id, [])

    if not edges:
        raise HTTPException(
            status_code=400,
            detail="Protocol ended - current node has no outgoing edges"
        )

    # Find matching edge based on response
    response_upper = request.response.upper()
    next_edge = None

    # Try exact match first
    for edge in edges:
        if edge.edge_label and edge.edge_label.upper() == response_upper:
            next_edge = edge
            break

    # Try partial match (e.g., "1" matches "YES_TOMORROW")
    if not next_edge:
        for edge in edges:
            if edge.edge_label and response_upper in edge.edge_label.upper():
                next_edge = edge
                break

    # Use default (unlabeled) edge
    if not next_edge:
        for edge in edges:
            if not edge.edge_label:
                next_edge = edge
                break

    # Fallback to first edge
    if not next_edge:
        next_edge = edges[0]

    # Get next node
    next_node = ctx["nodes_map"].get(next_edge.child_node_id)
    if not next_node:
        raise HTTPException(status_code=500, detail="Next node not found")

    # Update session time
    current_time = datetime.fromisoformat(session["current_time"])
    next_time = _calculate_next_time(
        next_node.timing_element_id,
        ctx["timings_map"],
        current_time
    )

    # Get message content
    message_text, media_url, quick_replies, expects_reply = _get_message_content(
        next_node,
        session["language"],
        ctx["templates_map"],
        ctx["adjacency"]
    )

    # Persist variable value if the edge carries a variable assignment
    participant_uuid: str | None = session.get("participant_uuid")
    participant_id: int | None = session.get("participant_id")

    if participant_id and next_edge.condition_expression_id is None:
        # Check if the current (source) node has an associated variable via its
        # exec_commands or the edge's SmsKeyword-style variable_id.  In our
        # graph model, edges don't carry variable_id directly — but the *source*
        # node's template may be collecting a value.  We look for variables
        # referenced by the node's answered_template or the node itself.
        await _maybe_persist_variable(
            db, current_node, next_edge, participant_id, request.response,
        )

    # Update session in Redis
    session["current_node_id"] = next_node.id
    session["current_time"] = next_time.isoformat()
    await save_session(request.session_id, session)

    # Persist current_node_id to participant extra_data for session recovery
    if participant_id:
        result = await db.execute(
            select(Participant).where(Participant.id == participant_id)
        )
        participant = result.scalar_one_or_none()
        if participant:
            extra = dict(participant.extra_data or {})
            extra["current_node_id"] = next_node.id
            extra["session_id"] = request.session_id
            extra["last_response"] = request.response
            extra["last_response_at"] = next_time.isoformat()
            participant.extra_data = extra
            await db.flush()

    # Calculate next scheduled time
    next_scheduled = _calculate_next_time(
        next_node.timing_element_id,
        ctx["timings_map"],
        next_time
    )

    return ProtocolSessionResponse(
        session_id=request.session_id,
        project_id=session["project_id"],
        project_name=ctx["project"].name,
        current_node_id=next_node.id,
        current_node_name=next_node.name,
        participant_uuid=participant_uuid,
        message=ProtocolMessage(
            message_text=message_text,
            media_url=media_url,
            quick_replies=quick_replies,
            expects_reply=expects_reply,
            is_terminal=next_node.is_terminal_node,
        ),
        session_time=next_time.isoformat(),
        next_scheduled_at=next_scheduled.isoformat() if next_scheduled != next_time else None,
    )


async def _maybe_persist_variable(
    db: AsyncSession,
    source_node: MessagingNode,
    edge: MessagingNodeEdge,
    participant_id: int,
    response_value: str,
) -> None:
    """Save participant's response as a variable value if the node collects one.

    The node graph can associate a variable with a node via exec_commands
    containing 'SET variable_name' or via the node's extra_data having a
    'variable_id' key. Edges may also reference variables through their
    condition expressions.
    """
    variable_id: int | None = None

    # Check node extra_data for an explicit variable_id
    if source_node.extra_data and source_node.extra_data.get("variable_id"):
        variable_id = int(source_node.extra_data["variable_id"])

    # Check exec_commands for SET directives (format: "SET <variable_id>")
    if not variable_id and source_node.exec_commands:
        for cmd in source_node.exec_commands.split(";"):
            cmd = cmd.strip()
            if cmd.upper().startswith("SET "):
                try:
                    variable_id = int(cmd.split()[1])
                except (IndexError, ValueError):
                    pass
                break

    if not variable_id:
        return

    # Upsert: update existing or create new
    from sqlalchemy import and_
    result = await db.execute(
        select(ParticipantVariableValue).where(
            and_(
                ParticipantVariableValue.participant_id == participant_id,
                ParticipantVariableValue.variable_id == variable_id,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.variable_value = response_value
    else:
        db.add(ParticipantVariableValue(
            participant_id=participant_id,
            variable_id=variable_id,
            variable_value=response_value,
        ))
    await db.flush()
    logger.info(
        "Saved variable %d = %r for participant %d",
        variable_id, response_value, participant_id,
    )


@router.get("/protocol/session/{session_id}")
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Get current session status.

    Example:
        GET /v1/protocol/session/{session_id}
        Headers: X-API-Key: YOUR_PROTOCOL_API_KEY
    """
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "project_id": session["project_id"],
        "current_node_id": session["current_node_id"],
        "language": session["language"],
        "current_time": session["current_time"],
        "created_at": session["created_at"],
        "participant_id": session.get("participant_id"),
        "participant_uuid": session.get("participant_uuid"),
    }


@router.delete("/protocol/session/{session_id}")
async def end_session(
    session_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict[str, str]:
    """
    End and delete a session.

    Example:
        DELETE /v1/protocol/session/{session_id}
        Headers: X-API-Key: YOUR_PROTOCOL_API_KEY
    """
    deleted = await delete_session(session_id)
    if deleted:
        return {"status": "deleted", "session_id": session_id}

    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/protocol/resume", response_model=ProtocolSessionResponse)
async def resume_protocol_session(
    request: ProtocolResumeRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> ProtocolSessionResponse:
    """Resume a protocol session for a participant.

    Looks up the participant by UUID, checks for an existing Redis session,
    and if expired, recreates the session from the participant's stored state.

    Example:
        POST /v1/protocol/resume
        Headers: X-API-Key: YOUR_PROTOCOL_API_KEY
        Body: {"participant_uuid": "abc-123"}
    """
    # Find participant
    result = await db.execute(
        select(Participant).where(Participant.uu_id == request.participant_uuid)
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    extra = participant.extra_data or {}
    current_node_id = extra.get("current_node_id")
    existing_session_id = extra.get("session_id")

    # Try to reuse existing Redis session
    if existing_session_id:
        session = await get_session(existing_session_id)
        if session:
            # Session still alive — return current state
            ctx = await _get_protocol_context(session["project_id"], db)
            node = ctx["nodes_map"].get(session["current_node_id"])
            if node:
                msg_text, media_url, qr, expects_reply = _get_message_content(
                    node, session["language"], ctx["templates_map"], ctx["adjacency"]
                )
                return ProtocolSessionResponse(
                    session_id=existing_session_id,
                    project_id=session["project_id"],
                    project_name=ctx["project"].name,
                    current_node_id=node.id,
                    current_node_name=node.name,
                    participant_uuid=participant.uu_id,
                    message=ProtocolMessage(
                        message_text=msg_text,
                        media_url=media_url,
                        quick_replies=qr,
                        expects_reply=expects_reply,
                        is_terminal=node.is_terminal_node,
                    ),
                    session_time=session["current_time"],
                )

    # No active session — recreate from participant's stored state
    if not current_node_id:
        raise HTTPException(
            status_code=404,
            detail="No active or recoverable session for this participant",
        )

    ctx = await _get_protocol_context(participant.project_id, db)
    node = ctx["nodes_map"].get(current_node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Stored node no longer exists in protocol")

    # Determine language
    language = request.language or ("es" if participant.current_language_id == 2 else "en")

    # Create a fresh Redis session
    session_id = str(uuid4())
    current_time = datetime.now(timezone.utc)

    session_data: dict[str, Any] = {
        "project_id": participant.project_id,
        "language": language,
        "current_node_id": node.id,
        "current_time": current_time.isoformat(),
        "created_at": current_time.isoformat(),
        "participant_id": participant.id,
        "participant_uuid": participant.uu_id,
        "resumed": True,
    }
    await save_session(session_id, session_data)

    # Update participant with new session_id
    extra["session_id"] = session_id
    participant.extra_data = extra
    await db.flush()

    msg_text, media_url, qr, expects_reply = _get_message_content(
        node, language, ctx["templates_map"], ctx["adjacency"]
    )

    return ProtocolSessionResponse(
        session_id=session_id,
        project_id=participant.project_id,
        project_name=ctx["project"].name,
        current_node_id=node.id,
        current_node_name=node.name,
        participant_uuid=participant.uu_id,
        message=ProtocolMessage(
            message_text=msg_text,
            media_url=media_url,
            quick_replies=qr,
            expects_reply=expects_reply,
            is_terminal=node.is_terminal_node,
        ),
        session_time=current_time.isoformat(),
    )
