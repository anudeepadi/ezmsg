"""Admin endpoints for testing protocol flows."""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.security.deps import require_admin
from app.models import (
    User, Project, Participant, MessagingNode, MessagingNodeEdge,
    MessageTemplate, MessageTemplateText, Variable, ParticipantVariableValue,
    ScheduledMessage, TimingElement
)

router = APIRouter(tags=["Protocol Testing"])


# ==================== Interactive Simulator Models ====================

class SimulatorStartRequest(BaseModel):
    """Request to start an interactive simulation."""
    language_id: int = 1
    start_time: Optional[str] = None  # ISO format, defaults to now


class SimulatorReplyRequest(BaseModel):
    """Request to reply in an interactive simulation."""
    current_node_id: int
    reply_value: str
    current_time: str  # ISO format
    language_id: int = 1


class QuickReply(BaseModel):
    """A quick reply option."""
    label: str
    value: str


class SimulatorMessage(BaseModel):
    """A message in the simulation."""
    node_id: int
    node_name: str
    display_name: Optional[str]
    message_text: Optional[str]
    media_url: Optional[str]
    scheduled_time: str
    delay_description: Optional[str]
    is_entry: bool
    is_terminal: bool
    quick_replies: list[QuickReply]
    available_edges: list[dict[str, Any]]
    expects_reply: bool


class ProtocolTestRequest(BaseModel):
    """Request to run a protocol test."""
    participant_name: str = "Test Participant"
    language_id: int = 1
    variables: dict[str, str] = {}


class NodeStep(BaseModel):
    """A step in the protocol flow."""
    node_id: int
    node_name: str
    message_text: str | None
    scheduled_time: datetime | None
    delay_minutes: int | None
    is_entry: bool
    is_terminal: bool
    edges: list[dict[str, Any]]


class ProtocolTestResponse(BaseModel):
    """Response from protocol test run."""
    project_id: int
    project_name: str
    participant_id: int
    total_nodes: int
    total_messages: int
    estimated_duration_days: int
    flow_steps: list[NodeStep]
    variables_used: list[dict[str, Any]]


@router.get("/{project_id}/overview")
async def get_protocol_overview(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Get an overview of the protocol structure for testing.
    """
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

    # Get edges
    node_ids = [n.id for n in nodes]
    edges_result = await db.execute(
        select(MessagingNodeEdge)
        .where(MessagingNodeEdge.parent_node_id.in_(node_ids))
    )
    edges = edges_result.scalars().all()

    # Get templates
    templates_result = await db.execute(
        select(MessageTemplate)
        .where(MessageTemplate.project_id == project_id)
    )
    templates = templates_result.scalars().all()

    # Get variables
    variables_result = await db.execute(
        select(Variable)
        .where(Variable.project_id == project_id)
    )
    variables = variables_result.scalars().all()

    # Find entry and terminal nodes
    entry_nodes = [n for n in nodes if n.is_entry_node]
    terminal_nodes = [n for n in nodes if n.is_terminal_node]

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "total_templates": len(templates),
        "total_variables": len(variables),
        "entry_nodes": [{"id": n.id, "name": n.name} for n in entry_nodes],
        "terminal_nodes": [{"id": n.id, "name": n.name} for n in terminal_nodes],
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "display_name": n.display_name,
                "is_entry": n.is_entry_node,
                "is_terminal": n.is_terminal_node,
                "template_id": n.template_id,
                "timing_element_id": n.timing_element_id
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "from_node": e.parent_node_id,
                "to_node": e.child_node_id,
                "label": e.edge_label
            }
            for e in edges
        ]
    }


@router.post("/{project_id}/run")
async def run_protocol_test(
    project_id: int,
    request: ProtocolTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Run a simulated protocol test.

    Creates a test participant and simulates the message flow,
    showing what messages would be sent and when.
    """
    # Get project
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all nodes with their templates
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
    if template_ids:
        templates_result = await db.execute(
            select(MessageTemplate)
            .options(selectinload(MessageTemplate.texts))
            .where(MessageTemplate.id.in_(template_ids))
        )
        templates = templates_result.scalars().all()
        templates_map = {t.id: t for t in templates}
    else:
        templates_map = {}

    # Get timing elements
    timing_ids = [n.timing_element_id for n in nodes if n.timing_element_id]
    if timing_ids:
        timing_result = await db.execute(
            select(TimingElement)
            .where(TimingElement.id.in_(timing_ids))
        )
        timings = timing_result.scalars().all()
        timings_map = {t.id: t for t in timings}
    else:
        timings_map = {}

    # Find entry node
    entry_nodes = [n for n in nodes if n.is_entry_node]
    if not entry_nodes:
        raise HTTPException(status_code=400, detail="No entry node found in protocol")

    # Simulate the flow starting from entry node
    flow_steps = []
    current_time = datetime.now()
    visited = set()

    def get_message_text(template_id: int | None, language_id: int) -> str | None:
        if not template_id or template_id not in templates_map:
            return None
        template = templates_map[template_id]
        for text in template.texts:
            if text.language_id == language_id:
                return text.message_text
        # Fallback to first text
        if template.texts:
            return template.texts[0].message_text
        return None

    def simulate_flow(node_id: int, scheduled_time: datetime, depth: int = 0):
        if depth > 100 or node_id in visited:  # Prevent infinite loops
            return

        visited.add(node_id)
        node = nodes_map.get(node_id)
        if not node:
            return

        # Get timing delay
        delay_minutes = None
        if node.timing_element_id and node.timing_element_id in timings_map:
            timing = timings_map[node.timing_element_id]
            if hasattr(timing, 'delay_minutes'):
                delay_minutes = timing.delay_minutes

        # Get message text
        message_text = get_message_text(node.template_id, request.language_id)

        # Get outgoing edges
        node_edges = adjacency.get(node_id, [])

        flow_steps.append({
            "step": len(flow_steps) + 1,
            "node_id": node.id,
            "node_name": node.name,
            "display_name": node.display_name,
            "message_text": message_text[:200] + "..." if message_text and len(message_text) > 200 else message_text,
            "scheduled_time": scheduled_time.isoformat(),
            "delay_minutes": delay_minutes,
            "is_entry": node.is_entry_node,
            "is_terminal": node.is_terminal_node,
            "edges": [
                {
                    "to_node_id": e.child_node_id,
                    "to_node_name": nodes_map[e.child_node_id].name if e.child_node_id in nodes_map else "Unknown",
                    "label": e.edge_label
                }
                for e in node_edges
            ]
        })

        # Continue to first edge (default path) for simulation
        if node_edges and not node.is_terminal_node:
            next_edge = node_edges[0]
            next_time = scheduled_time + timedelta(minutes=delay_minutes or 60)
            simulate_flow(next_edge.child_node_id, next_time, depth + 1)

    # Start simulation from entry node
    simulate_flow(entry_nodes[0].id, current_time)

    # Calculate estimated duration
    if len(flow_steps) >= 2:
        first_time = datetime.fromisoformat(flow_steps[0]["scheduled_time"])
        last_time = datetime.fromisoformat(flow_steps[-1]["scheduled_time"])
        duration_days = (last_time - first_time).days
    else:
        duration_days = 0

    # Get variables used in the project
    variables_result = await db.execute(
        select(Variable)
        .where(Variable.project_id == project_id)
    )
    variables = variables_result.scalars().all()

    return {
        "project_id": project_id,
        "project_name": project.name,
        "test_started_at": current_time.isoformat(),
        "total_nodes_in_flow": len(flow_steps),
        "total_nodes_in_project": len(nodes),
        "estimated_duration_days": duration_days,
        "language_id": request.language_id,
        "flow_steps": flow_steps,
        "variables": [
            {
                "id": v.id,
                "name": v.name,
                "display_name": v.display_name,
                "type": v.type,
                "default_value": v.default_value
            }
            for v in variables
        ]
    }


@router.post("/{project_id}/create-test-participant")
async def create_test_participant(
    project_id: int,
    request: ProtocolTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Create a test participant and enroll them in the protocol.

    This creates actual scheduled messages that can be viewed in the scheduler.
    """
    from uuid import uuid4

    # Get project
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create test participant
    participant = Participant(
        uu_id=str(uuid4()),
        project_id=project_id,
        external_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        status="ENROLLED",
        channel_type="SMS",
        language_id=request.language_id,
        is_test_participant=True,
        enrolled_at=datetime.now()
    )
    db.add(participant)
    await db.flush()

    # Get entry node
    entry_result = await db.execute(
        select(MessagingNode)
        .where(MessagingNode.project_id == project_id)
        .where(MessagingNode.is_entry_node == True)
    )
    entry_node = entry_result.scalar_one_or_none()

    if not entry_node:
        raise HTTPException(status_code=400, detail="No entry node found")

    # Schedule first message
    scheduled_msg = ScheduledMessage(
        participant_id=participant.id,
        node_id=entry_node.id,
        template_id=entry_node.template_id,
        status="PENDING",
        scheduled_at=datetime.now() + timedelta(minutes=1),
        attempt_count=0
    )
    db.add(scheduled_msg)

    await db.commit()

    return {
        "message": "Test participant created and enrolled",
        "participant_id": participant.id,
        "participant_uuid": participant.uu_id,
        "external_id": participant.external_id,
        "first_message_scheduled_at": scheduled_msg.scheduled_at.isoformat(),
        "entry_node": entry_node.name
    }


# ==================== Interactive Simulator Endpoints ====================

async def _get_simulator_context(project_id: int, db: AsyncSession) -> dict[str, Any]:
    """Load all necessary data for simulation."""
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


def _get_template_content(
    template_id: int | None,
    language_id: int,
    templates_map: dict[int, MessageTemplate]
) -> tuple[str | None, str | None, list[QuickReply]]:
    """Get message text, media URL, and quick replies for a template."""
    if not template_id or template_id not in templates_map:
        return None, None, []

    template = templates_map[template_id]
    text_obj = None

    # Find text for language
    for t in template.texts:
        if t.language_id == language_id:
            text_obj = t
            break

    # Fallback to first text
    if not text_obj and template.texts:
        text_obj = template.texts[0]

    if not text_obj:
        return None, None, []

    # Parse quick replies
    quick_replies = []
    if text_obj.quick_replies:
        for qr in text_obj.quick_replies:
            if isinstance(qr, dict) and "label" in qr and "value" in qr:
                quick_replies.append(QuickReply(label=qr["label"], value=qr["value"]))

    return text_obj.message_text, text_obj.media_url, quick_replies


def _calculate_timing(
    timing_element_id: int | None,
    timings_map: dict[int, TimingElement],
    base_time: datetime
) -> tuple[datetime, str | None]:
    """Calculate the scheduled time based on timing element."""
    if not timing_element_id or timing_element_id not in timings_map:
        return base_time, None

    timing = timings_map[timing_element_id]

    # Calculate offset
    offset = timedelta(
        days=timing.offset_days,
        hours=timing.offset_hours,
        minutes=timing.offset_minutes,
        seconds=timing.offset_seconds
    )

    scheduled_time = base_time + offset

    # Apply overwritten time if specified
    if timing.overwrite_time and timing.overwritten_hours is not None:
        scheduled_time = scheduled_time.replace(
            hour=timing.overwritten_hours,
            minute=timing.overwritten_minutes or 0,
            second=0,
            microsecond=0
        )

    # Build delay description
    parts = []
    if timing.offset_days:
        parts.append(f"{timing.offset_days} day{'s' if timing.offset_days > 1 else ''}")
    if timing.offset_hours:
        parts.append(f"{timing.offset_hours} hour{'s' if timing.offset_hours > 1 else ''}")
    if timing.offset_minutes:
        parts.append(f"{timing.offset_minutes} minute{'s' if timing.offset_minutes > 1 else ''}")

    delay_desc = None
    if parts:
        delay_desc = " + ".join(parts)
        if timing.overwrite_time and timing.overwritten_hours is not None:
            h = timing.overwritten_hours
            m = timing.overwritten_minutes or 0
            am_pm = "AM" if h < 12 else "PM"
            h12 = h if h <= 12 else h - 12
            if h12 == 0:
                h12 = 12
            delay_desc += f" (at {h12}:{m:02d} {am_pm})"

    return scheduled_time, delay_desc


def _build_message(
    node: MessagingNode,
    scheduled_time: datetime,
    delay_desc: str | None,
    language_id: int,
    templates_map: dict,
    adjacency: dict,
    nodes_map: dict
) -> dict[str, Any]:
    """Build a simulator message from a node."""
    message_text, media_url, quick_replies = _get_template_content(
        node.template_id, language_id, templates_map
    )

    # Get outgoing edges
    edges = adjacency.get(node.id, [])
    available_edges = [
        {
            "to_node_id": e.child_node_id,
            "to_node_name": nodes_map[e.child_node_id].name if e.child_node_id in nodes_map else "Unknown",
            "to_display_name": nodes_map[e.child_node_id].display_name if e.child_node_id in nodes_map else None,
            "label": e.edge_label,
        }
        for e in edges
    ]

    # Determine if reply is expected
    # Reply expected if there are multiple edges with labels, or quick replies
    has_labeled_edges = any(e.edge_label for e in edges)
    expects_reply = bool(quick_replies) or has_labeled_edges

    return {
        "node_id": node.id,
        "node_name": node.name,
        "display_name": node.display_name,
        "message_text": message_text,
        "media_url": media_url,
        "scheduled_time": scheduled_time.isoformat(),
        "delay_description": delay_desc,
        "is_entry": node.is_entry_node,
        "is_terminal": node.is_terminal_node,
        "quick_replies": [qr.model_dump() for qr in quick_replies],
        "available_edges": available_edges,
        "expects_reply": expects_reply,
    }


@router.post("/{project_id}/simulate/start")
async def start_simulation(
    project_id: int,
    request: SimulatorStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Start an interactive protocol simulation.

    Returns the entry node message with quick reply options.
    """
    ctx = await _get_simulator_context(project_id, db)

    # Find entry node
    entry_node = None
    for node in ctx["nodes_map"].values():
        if node.is_entry_node:
            entry_node = node
            break

    if not entry_node:
        raise HTTPException(status_code=400, detail="No entry node found in protocol")

    # Parse start time
    if request.start_time:
        start_time = datetime.fromisoformat(request.start_time)
    else:
        start_time = datetime.now()

    # Calculate scheduled time for entry node
    scheduled_time, delay_desc = _calculate_timing(
        entry_node.timing_element_id,
        ctx["timings_map"],
        start_time
    )

    # Build message
    message = _build_message(
        entry_node,
        scheduled_time,
        delay_desc,
        request.language_id,
        ctx["templates_map"],
        ctx["adjacency"],
        ctx["nodes_map"]
    )

    return {
        "project_id": project_id,
        "project_name": ctx["project"].name,
        "simulation_started_at": start_time.isoformat(),
        "language_id": request.language_id,
        "message": message,
    }


@router.post("/{project_id}/simulate/reply")
async def simulate_reply(
    project_id: int,
    request: SimulatorReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Process a reply in the simulation and return the next message.

    Matches the reply value to edge labels to determine the next node.
    """
    ctx = await _get_simulator_context(project_id, db)

    # Get current node
    current_node = ctx["nodes_map"].get(request.current_node_id)
    if not current_node:
        raise HTTPException(status_code=404, detail="Current node not found")

    # Parse current time
    current_time = datetime.fromisoformat(request.current_time)

    # Get outgoing edges
    edges = ctx["adjacency"].get(request.current_node_id, [])

    if not edges:
        return {
            "project_id": project_id,
            "reply_received": request.reply_value,
            "reply_received_at": current_time.isoformat(),
            "message": None,
            "end_reason": "terminal_node" if current_node.is_terminal_node else "no_outgoing_edges",
        }

    # Find matching edge
    next_edge = None
    for edge in edges:
        if edge.edge_label and edge.edge_label.upper() == request.reply_value.upper():
            next_edge = edge
            break

    # If no labeled match, use the first edge (default path)
    if not next_edge:
        # Check if there's a default (unlabeled) edge
        for edge in edges:
            if not edge.edge_label:
                next_edge = edge
                break
        # Otherwise use first edge
        if not next_edge:
            next_edge = edges[0]

    # Get next node
    next_node = ctx["nodes_map"].get(next_edge.child_node_id)
    if not next_node:
        raise HTTPException(status_code=500, detail="Next node not found")

    # Calculate timing from current time
    scheduled_time, delay_desc = _calculate_timing(
        next_node.timing_element_id,
        ctx["timings_map"],
        current_time
    )

    # Build message
    message = _build_message(
        next_node,
        scheduled_time,
        delay_desc,
        request.language_id,
        ctx["templates_map"],
        ctx["adjacency"],
        ctx["nodes_map"]
    )

    return {
        "project_id": project_id,
        "reply_received": request.reply_value,
        "reply_received_at": current_time.isoformat(),
        "matched_edge_label": next_edge.edge_label,
        "message": message,
    }


@router.post("/{project_id}/simulate/advance")
async def simulate_advance(
    project_id: int,
    request: SimulatorReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Advance to the next node without a specific reply (auto-continue).

    Used for nodes that don't expect a reply.
    """
    # Use the same logic as reply but with empty/default reply
    request.reply_value = ""
    return await simulate_reply(project_id, request, db, current_user)
