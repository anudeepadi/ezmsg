"""Public API for protocol interaction via API key."""

import os
from datetime import datetime, timedelta
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
    MessageTemplate, MessageTemplateText, TimingElement
)

router = APIRouter(tags=["Protocol API"])

# API key from environment variable (fallback to test key for local development)
API_KEY = os.getenv("PROTOCOL_API_KEY", "iquit0-test-key-12345")


class ProtocolStartRequest(BaseModel):
    """Request to start a protocol session."""
    project_id: int
    language: str = "en"  # "en" or "es"
    initial_response: Optional[str] = None  # e.g., "iquit0" for immediate quit


class ProtocolResponseRequest(BaseModel):
    """Request to send a response in an ongoing session."""
    session_id: str
    response: str  # User's response (e.g., "1", "YES", "NO")


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
    message: ProtocolMessage
    session_time: str
    next_scheduled_at: Optional[str] = None


# In-memory session storage (use Redis in production)
SESSIONS: dict[str, dict[str, Any]] = {}


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header."""
    if x_api_key != API_KEY:
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
        Headers: X-API-Key: iquit0-test-key-12345
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

    # Create session
    session_id = str(uuid4())
    current_time = datetime.now()

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

    # Store session
    SESSIONS[session_id] = {
        "project_id": request.project_id,
        "language": request.language,
        "current_node_id": current_node.id,
        "current_time": current_time.isoformat(),
        "created_at": datetime.now().isoformat(),
    }

    return ProtocolSessionResponse(
        session_id=session_id,
        project_id=request.project_id,
        project_name=ctx["project"].name,
        current_node_id=current_node.id,
        current_node_name=current_node.name,
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
        Headers: X-API-Key: iquit0-test-key-12345
        Body: {
            "session_id": "uuid-here",
            "response": "1"
        }
    """
    # Get session
    session = SESSIONS.get(request.session_id)
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

    # Update session
    session["current_node_id"] = next_node.id
    session["current_time"] = next_time.isoformat()

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


@router.get("/protocol/session/{session_id}")
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Get current session status.

    Example:
        GET /v1/protocol/session/{session_id}
        Headers: X-API-Key: iquit0-test-key-12345
    """
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "project_id": session["project_id"],
        "current_node_id": session["current_node_id"],
        "language": session["language"],
        "current_time": session["current_time"],
        "created_at": session["created_at"],
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
        Headers: X-API-Key: iquit0-test-key-12345
    """
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        return {"status": "deleted", "session_id": session_id}

    raise HTTPException(status_code=404, detail="Session not found")
