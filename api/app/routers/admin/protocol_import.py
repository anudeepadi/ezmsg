"""Protocol import/export endpoints for admin dashboard."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models import (
    Project, MessagingNode, MessagingNodeEdge,
    MessageTemplate, MessageTemplateText,
    TimingElement, Variable, SmsKeyword,
    ConditionalExpression, ConditionalExpressionVariable,
)
from app.models.user import User
from app.security.deps import require_researcher_or_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Export ────────────────────────────────────────────────────────────────


@router.get("/projects/{project_id}/export")
async def export_protocol(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> dict[str, Any]:
    """Export a project's full protocol as JSON.

    Includes: nodes, edges, templates (with texts), timing elements,
    variables, keywords, and conditional expressions.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load all related data
    nodes = (await db.execute(
        select(MessagingNode)
        .where(MessagingNode.project_id == project_id)
        .order_by(MessagingNode.node_order)
    )).scalars().all()

    node_ids = [n.id for n in nodes]
    edges = (await db.execute(
        select(MessagingNodeEdge)
        .where(MessagingNodeEdge.parent_node_id.in_(node_ids))
        .order_by(MessagingNodeEdge.edge_order)
    )).scalars().all() if node_ids else []

    templates = (await db.execute(
        select(MessageTemplate)
        .options(selectinload(MessageTemplate.texts))
        .where(MessageTemplate.project_id == project_id)
    )).scalars().all()

    timings = (await db.execute(
        select(TimingElement)
        .where(TimingElement.project_id == project_id)
    )).scalars().all()

    variables = (await db.execute(
        select(Variable)
        .where(Variable.project_id == project_id)
    )).scalars().all()

    keywords = (await db.execute(
        select(SmsKeyword)
        .where(SmsKeyword.project_id == project_id)
    )).scalars().all()

    conditions = (await db.execute(
        select(ConditionalExpression)
        .options(selectinload(ConditionalExpression.expression_variables))
        .where(ConditionalExpression.project_id == project_id)
    )).scalars().all()

    # Build ID -> name maps for references
    template_id_map = {t.id: t.name for t in templates}
    timing_id_map = {t.id: t.name for t in timings}
    variable_id_map = {v.id: v.name for v in variables}
    node_id_map = {n.id: n.name for n in nodes}
    condition_id_map = {c.id: c.name for c in conditions}

    return {
        "version": "1.0",
        "project": {
            "name": project.name,
            "description": project.description,
            "settings": project.settings if hasattr(project, "settings") else {},
        },
        "variables": [
            {
                "name": v.name,
                "display_name": v.display_name,
                "type": v.type.value if hasattr(v.type, "value") else str(v.type),
                "source_type": v.source_type.value if hasattr(v.source_type, "value") else str(v.source_type),
                "default_value": v.default_value,
                "description": v.description,
            }
            for v in variables
        ],
        "timing_elements": [
            {
                "name": t.name,
                "description": t.description,
                "offset_direction": t.offset_direction,
                "offset_days": t.offset_days,
                "offset_hours": t.offset_hours,
                "offset_minutes": t.offset_minutes,
                "offset_seconds": t.offset_seconds,
                "overwrite_time": t.overwrite_time,
                "overwritten_hours": t.overwritten_hours,
                "overwritten_minutes": t.overwritten_minutes,
                "time_variable": variable_id_map.get(t.time_variable_id),
            }
            for t in timings
        ],
        "templates": [
            {
                "name": t.name,
                "type": t.type,
                "description": t.description,
                "texts": [
                    {
                        "language_id": txt.language_id,
                        "message_text": txt.message_text,
                        "media_url": txt.media_url,
                        "media_type": txt.media_type,
                        "quick_replies": txt.quick_replies or [],
                    }
                    for txt in t.texts
                ],
            }
            for t in templates
        ],
        "conditional_expressions": [
            {
                "name": c.name,
                "description": c.description,
                "condition_text": c.condition_text,
                "variables": [
                    variable_id_map.get(ev.variable_id, "")
                    for ev in c.expression_variables
                ],
            }
            for c in conditions
        ],
        "nodes": [
            {
                "name": n.name,
                "display_name": n.display_name,
                "description": n.description,
                "is_entry_node": n.is_entry_node,
                "is_terminal_node": n.is_terminal_node,
                "node_order": n.node_order,
                "exec_commands": n.exec_commands,
                "template": template_id_map.get(n.template_id),
                "answered_template": template_id_map.get(n.answered_template_id),
                "timing_element": timing_id_map.get(n.timing_element_id),
                "conditional_expression": condition_id_map.get(n.conditional_expression_id),
                "timing_variable": variable_id_map.get(n.timing_variable_id),
                "extra_data": n.extra_data or {},
            }
            for n in nodes
        ],
        "edges": [
            {
                "parent_node": node_id_map.get(e.parent_node_id, ""),
                "child_node": node_id_map.get(e.child_node_id, ""),
                "edge_label": e.edge_label,
                "edge_order": e.edge_order,
                "condition_expression": condition_id_map.get(e.condition_expression_id),
            }
            for e in edges
        ],
        "keywords": [
            {
                "keyword_text": k.keyword_text,
                "keyword_name": k.keyword_name,
                "keyword_action_type": k.keyword_action_type,
                "language_id": k.language_id,
                "variable": variable_id_map.get(k.variable_id),
                "variable_value": k.variable_value,
                "response_template": template_id_map.get(k.response_template_id),
                "messaging_node": node_id_map.get(k.messaging_node_id),
                "message_pool": k.message_pool,
                "is_active": k.is_active,
            }
            for k in keywords
        ],
    }


# ── Import ────────────────────────────────────────────────────────────────


class ImportResult(BaseModel):
    """Result summary from protocol import."""
    variables_created: int = 0
    timing_elements_created: int = 0
    templates_created: int = 0
    conditions_created: int = 0
    nodes_created: int = 0
    edges_created: int = 0
    keywords_created: int = 0


@router.post("/projects/{project_id}/import", response_model=ImportResult)
async def import_protocol(
    project_id: int,
    protocol: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> ImportResult:
    """Import a protocol definition into a project.

    Accepts the same JSON format produced by the export endpoint.
    Uses name-based deduplication — existing objects with the same
    name are skipped, not overwritten.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = ImportResult()

    # 1. Variables
    variable_name_to_id: dict[str, int] = {}
    for var_def in protocol.get("variables", []):
        existing = (await db.execute(
            select(Variable).where(
                Variable.project_id == project_id,
                Variable.name == var_def["name"],
            )
        )).scalar_one_or_none()
        if existing:
            variable_name_to_id[var_def["name"]] = existing.id
            continue
        v = Variable(
            project_id=project_id,
            name=var_def["name"],
            display_name=var_def.get("display_name"),
            type=var_def.get("type", "STRING"),
            source_type=var_def.get("source_type", "MANUAL"),
            default_value=var_def.get("default_value"),
            description=var_def.get("description"),
        )
        db.add(v)
        await db.flush()
        variable_name_to_id[var_def["name"]] = v.id
        result.variables_created += 1

    # 2. Timing elements
    timing_name_to_id: dict[str, int] = {}
    for t_def in protocol.get("timing_elements", []):
        existing = (await db.execute(
            select(TimingElement).where(
                TimingElement.project_id == project_id,
                TimingElement.name == t_def["name"],
            )
        )).scalar_one_or_none()
        if existing:
            timing_name_to_id[t_def["name"]] = existing.id
            continue
        t = TimingElement(
            project_id=project_id,
            name=t_def["name"],
            description=t_def.get("description"),
            offset_direction=t_def.get("offset_direction", "AFTER"),
            offset_days=t_def.get("offset_days", 0),
            offset_hours=t_def.get("offset_hours", 0),
            offset_minutes=t_def.get("offset_minutes", 0),
            offset_seconds=t_def.get("offset_seconds", 0),
            overwrite_time=t_def.get("overwrite_time", False),
            overwritten_hours=t_def.get("overwritten_hours"),
            overwritten_minutes=t_def.get("overwritten_minutes"),
            time_variable_id=variable_name_to_id.get(t_def.get("time_variable")) if t_def.get("time_variable") else None,
        )
        db.add(t)
        await db.flush()
        timing_name_to_id[t_def["name"]] = t.id
        result.timing_elements_created += 1

    # 3. Templates
    template_name_to_id: dict[str, int] = {}
    for tmpl_def in protocol.get("templates", []):
        existing = (await db.execute(
            select(MessageTemplate).where(
                MessageTemplate.project_id == project_id,
                MessageTemplate.name == tmpl_def["name"],
            )
        )).scalar_one_or_none()
        if existing:
            template_name_to_id[tmpl_def["name"]] = existing.id
            continue
        tmpl = MessageTemplate(
            project_id=project_id,
            name=tmpl_def["name"],
            type=tmpl_def.get("type", "STANDARD"),
            description=tmpl_def.get("description"),
        )
        db.add(tmpl)
        await db.flush()
        for txt in tmpl_def.get("texts", []):
            db.add(MessageTemplateText(
                template_id=tmpl.id,
                language_id=txt["language_id"],
                message_text=txt.get("message_text"),
                media_url=txt.get("media_url"),
                media_type=txt.get("media_type"),
                quick_replies=txt.get("quick_replies", []),
            ))
        await db.flush()
        template_name_to_id[tmpl_def["name"]] = tmpl.id
        result.templates_created += 1

    # 4. Conditional expressions
    condition_name_to_id: dict[str, int] = {}
    for c_def in protocol.get("conditional_expressions", []):
        existing = (await db.execute(
            select(ConditionalExpression).where(
                ConditionalExpression.project_id == project_id,
                ConditionalExpression.name == c_def["name"],
            )
        )).scalar_one_or_none()
        if existing:
            condition_name_to_id[c_def["name"]] = existing.id
            continue
        ce = ConditionalExpression(
            project_id=project_id,
            name=c_def["name"],
            description=c_def.get("description"),
            condition_text=c_def["condition_text"],
        )
        db.add(ce)
        await db.flush()
        for var_name in c_def.get("variables", []):
            if var_name and var_name in variable_name_to_id:
                db.add(ConditionalExpressionVariable(
                    conditional_expression_id=ce.id,
                    variable_id=variable_name_to_id[var_name],
                ))
        await db.flush()
        condition_name_to_id[c_def["name"]] = ce.id
        result.conditions_created += 1

    # 5. Nodes
    node_name_to_id: dict[str, int] = {}
    for n_def in protocol.get("nodes", []):
        existing = (await db.execute(
            select(MessagingNode).where(
                MessagingNode.project_id == project_id,
                MessagingNode.name == n_def["name"],
            )
        )).scalar_one_or_none()
        if existing:
            node_name_to_id[n_def["name"]] = existing.id
            continue
        node = MessagingNode(
            project_id=project_id,
            name=n_def["name"],
            display_name=n_def.get("display_name"),
            description=n_def.get("description"),
            is_entry_node=n_def.get("is_entry_node", False),
            is_terminal_node=n_def.get("is_terminal_node", False),
            node_order=n_def.get("node_order", 0),
            exec_commands=n_def.get("exec_commands"),
            template_id=template_name_to_id.get(n_def.get("template")) if n_def.get("template") else None,
            answered_template_id=template_name_to_id.get(n_def.get("answered_template")) if n_def.get("answered_template") else None,
            timing_element_id=timing_name_to_id.get(n_def.get("timing_element")) if n_def.get("timing_element") else None,
            conditional_expression_id=condition_name_to_id.get(n_def.get("conditional_expression")) if n_def.get("conditional_expression") else None,
            timing_variable_id=variable_name_to_id.get(n_def.get("timing_variable")) if n_def.get("timing_variable") else None,
            extra_data=n_def.get("extra_data", {}),
        )
        db.add(node)
        await db.flush()
        node_name_to_id[n_def["name"]] = node.id
        result.nodes_created += 1

    # 6. Edges
    for e_def in protocol.get("edges", []):
        parent_id = node_name_to_id.get(e_def.get("parent_node"))
        child_id = node_name_to_id.get(e_def.get("child_node"))
        if not parent_id or not child_id:
            logger.warning(
                "Skipping edge %s -> %s: node not found",
                e_def.get("parent_node"), e_def.get("child_node"),
            )
            continue
        edge = MessagingNodeEdge(
            parent_node_id=parent_id,
            child_node_id=child_id,
            edge_label=e_def.get("edge_label"),
            edge_order=e_def.get("edge_order", 0),
            condition_expression_id=condition_name_to_id.get(e_def.get("condition_expression")) if e_def.get("condition_expression") else None,
        )
        db.add(edge)
        result.edges_created += 1

    # 7. Keywords
    for k_def in protocol.get("keywords", []):
        existing = (await db.execute(
            select(SmsKeyword).where(
                SmsKeyword.project_id == project_id,
                SmsKeyword.keyword_text == k_def["keyword_text"],
            )
        )).scalar_one_or_none()
        if existing:
            continue
        kw = SmsKeyword(
            project_id=project_id,
            keyword_text=k_def["keyword_text"],
            keyword_name=k_def.get("keyword_name", k_def["keyword_text"]),
            keyword_action_type=k_def.get("keyword_action_type", ""),
            language_id=k_def.get("language_id"),
            variable_id=variable_name_to_id.get(k_def.get("variable")) if k_def.get("variable") else None,
            variable_value=k_def.get("variable_value"),
            response_template_id=template_name_to_id.get(k_def.get("response_template")) if k_def.get("response_template") else None,
            messaging_node_id=node_name_to_id.get(k_def.get("messaging_node")) if k_def.get("messaging_node") else None,
            message_pool=k_def.get("message_pool"),
            is_active=k_def.get("is_active", True),
        )
        db.add(kw)
        result.keywords_created += 1

    await db.flush()

    logger.info(
        "Protocol import for project %d: %d vars, %d timings, %d templates, "
        "%d conditions, %d nodes, %d edges, %d keywords",
        project_id, result.variables_created, result.timing_elements_created,
        result.templates_created, result.conditions_created,
        result.nodes_created, result.edges_created, result.keywords_created,
    )

    return result
