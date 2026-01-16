"""Nodes admin router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.messaging_node import MessagingNode, MessagingNodeEdge, NodeTimingObjectType
from app.models.project import Project
from app.models.user import User
from app.security.deps import get_current_active_user

router = APIRouter()


class NodeCreate(BaseModel):
    """Node creation schema."""
    project_id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_terminal_node: bool = False
    is_entry_node: bool = False
    template_id: Optional[int] = None
    timing_element_id: Optional[int] = None
    conditional_expression_id: Optional[int] = None
    node_order: int = 0


class NodeUpdate(BaseModel):
    """Node update schema."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_terminal_node: Optional[bool] = None
    is_entry_node: Optional[bool] = None
    template_id: Optional[int] = None
    timing_element_id: Optional[int] = None
    node_order: Optional[int] = None


class EdgeCreate(BaseModel):
    """Edge creation schema."""
    parent_node_id: int
    child_node_id: int
    edge_label: Optional[str] = None
    edge_order: int = 0


class NodeResponse(BaseModel):
    """Node response schema."""
    id: int
    project_id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    is_terminal_node: bool
    is_entry_node: bool
    template_id: Optional[int]
    timing_element_id: Optional[int]
    conditional_expression_id: Optional[int]
    node_order: int
    outgoing_edge_count: int = 0
    incoming_edge_count: int = 0

    class Config:
        from_attributes = True


class EdgeResponse(BaseModel):
    """Edge response schema."""
    id: int
    parent_node_id: int
    child_node_id: int
    edge_label: Optional[str]
    edge_order: int

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    """Full graph response."""
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]


@router.get("/project/{project_id}", response_model=List[NodeResponse])
async def list_nodes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> List[NodeResponse]:
    """List nodes for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        List of nodes
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(MessagingNode)
        .options(
            selectinload(MessagingNode.outgoing_edges),
            selectinload(MessagingNode.incoming_edges),
        )
        .where(
            MessagingNode.project_id == project_id,
            MessagingNode.removed_at.is_(None),
        )
        .order_by(MessagingNode.node_order, MessagingNode.name)
    )
    nodes = result.scalars().all()

    return [
        NodeResponse(
            id=n.id,
            project_id=n.project_id,
            name=n.name,
            display_name=n.display_name,
            description=n.description,
            is_terminal_node=n.is_terminal_node,
            is_entry_node=n.is_entry_node,
            template_id=n.template_id,
            timing_element_id=n.timing_element_id,
            conditional_expression_id=n.conditional_expression_id,
            node_order=n.node_order,
            outgoing_edge_count=len(n.outgoing_edges),
            incoming_edge_count=len(n.incoming_edges),
        )
        for n in nodes
    ]


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> NodeResponse:
    """Create a new messaging node.

    Args:
        data: Node data
        db: Database session
        user: Current user

    Returns:
        Created node
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == data.project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    node = MessagingNode(
        project_id=data.project_id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        is_terminal_node=data.is_terminal_node,
        is_entry_node=data.is_entry_node,
        template_id=data.template_id,
        timing_element_id=data.timing_element_id,
        conditional_expression_id=data.conditional_expression_id,
        node_order=data.node_order,
    )
    db.add(node)
    await db.flush()
    await db.refresh(node)

    return NodeResponse(
        id=node.id,
        project_id=node.project_id,
        name=node.name,
        display_name=node.display_name,
        description=node.description,
        is_terminal_node=node.is_terminal_node,
        is_entry_node=node.is_entry_node,
        template_id=node.template_id,
        timing_element_id=node.timing_element_id,
        conditional_expression_id=node.conditional_expression_id,
        node_order=node.node_order,
    )


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> NodeResponse:
    """Get a specific node.

    Args:
        node_id: Node ID
        db: Database session
        user: Current user

    Returns:
        Node details
    """
    result = await db.execute(
        select(MessagingNode)
        .options(
            selectinload(MessagingNode.project),
            selectinload(MessagingNode.outgoing_edges),
            selectinload(MessagingNode.incoming_edges),
        )
        .where(MessagingNode.id == node_id, MessagingNode.removed_at.is_(None))
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if user.role.value != "admin" and node.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return NodeResponse(
        id=node.id,
        project_id=node.project_id,
        name=node.name,
        display_name=node.display_name,
        description=node.description,
        is_terminal_node=node.is_terminal_node,
        is_entry_node=node.is_entry_node,
        template_id=node.template_id,
        timing_element_id=node.timing_element_id,
        conditional_expression_id=node.conditional_expression_id,
        node_order=node.node_order,
        outgoing_edge_count=len(node.outgoing_edges),
        incoming_edge_count=len(node.incoming_edges),
    )


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: int,
    data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> NodeResponse:
    """Update a node.

    Args:
        node_id: Node ID
        data: Update data
        db: Database session
        user: Current user

    Returns:
        Updated node
    """
    result = await db.execute(
        select(MessagingNode)
        .options(selectinload(MessagingNode.project))
        .where(MessagingNode.id == node_id, MessagingNode.removed_at.is_(None))
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if user.role.value != "admin" and node.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    if data.name is not None:
        node.name = data.name
    if data.display_name is not None:
        node.display_name = data.display_name
    if data.description is not None:
        node.description = data.description
    if data.is_terminal_node is not None:
        node.is_terminal_node = data.is_terminal_node
    if data.is_entry_node is not None:
        node.is_entry_node = data.is_entry_node
    if data.template_id is not None:
        node.template_id = data.template_id
    if data.timing_element_id is not None:
        node.timing_element_id = data.timing_element_id
    if data.node_order is not None:
        node.node_order = data.node_order

    await db.flush()
    await db.refresh(node)

    return NodeResponse(
        id=node.id,
        project_id=node.project_id,
        name=node.name,
        display_name=node.display_name,
        description=node.description,
        is_terminal_node=node.is_terminal_node,
        is_entry_node=node.is_entry_node,
        template_id=node.template_id,
        timing_element_id=node.timing_element_id,
        conditional_expression_id=node.conditional_expression_id,
        node_order=node.node_order,
    )


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> None:
    """Delete a node."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(MessagingNode)
        .options(selectinload(MessagingNode.project))
        .where(MessagingNode.id == node_id, MessagingNode.removed_at.is_(None))
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if user.role.value != "admin" and node.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    node.removed_at = datetime.now(timezone.utc)


@router.get("/project/{project_id}/graph", response_model=GraphResponse)
async def get_project_graph(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> GraphResponse:
    """Get the full node graph for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Full graph with nodes and edges
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get nodes
    nodes_result = await db.execute(
        select(MessagingNode)
        .options(
            selectinload(MessagingNode.outgoing_edges),
            selectinload(MessagingNode.incoming_edges),
        )
        .where(
            MessagingNode.project_id == project_id,
            MessagingNode.removed_at.is_(None),
        )
    )
    nodes = nodes_result.scalars().all()

    # Get edges
    edges_result = await db.execute(
        select(MessagingNodeEdge)
        .join(MessagingNode, MessagingNodeEdge.parent_node_id == MessagingNode.id)
        .where(
            MessagingNode.project_id == project_id,
            MessagingNodeEdge.removed_at.is_(None),
        )
    )
    edges = edges_result.scalars().all()

    return GraphResponse(
        nodes=[
            NodeResponse(
                id=n.id,
                project_id=n.project_id,
                name=n.name,
                display_name=n.display_name,
                description=n.description,
                is_terminal_node=n.is_terminal_node,
                is_entry_node=n.is_entry_node,
                template_id=n.template_id,
                timing_element_id=n.timing_element_id,
                conditional_expression_id=n.conditional_expression_id,
                node_order=n.node_order,
                outgoing_edge_count=len(n.outgoing_edges),
                incoming_edge_count=len(n.incoming_edges),
            )
            for n in nodes
        ],
        edges=[
            EdgeResponse(
                id=e.id,
                parent_node_id=e.parent_node_id,
                child_node_id=e.child_node_id,
                edge_label=e.edge_label,
                edge_order=e.edge_order,
            )
            for e in edges
        ],
    )


@router.post("/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
async def create_edge(
    data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> EdgeResponse:
    """Create an edge between two nodes.

    Args:
        data: Edge data
        db: Database session
        user: Current user

    Returns:
        Created edge
    """
    # Verify parent node exists and user has access
    parent_result = await db.execute(
        select(MessagingNode)
        .options(selectinload(MessagingNode.project))
        .where(MessagingNode.id == data.parent_node_id, MessagingNode.removed_at.is_(None))
    )
    parent = parent_result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent node not found")

    if user.role.value != "admin" and parent.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Verify child node exists in same project
    child_result = await db.execute(
        select(MessagingNode).where(
            MessagingNode.id == data.child_node_id,
            MessagingNode.project_id == parent.project_id,
            MessagingNode.removed_at.is_(None),
        )
    )
    if not child_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Child node not found in same project")

    edge = MessagingNodeEdge(
        parent_node_id=data.parent_node_id,
        child_node_id=data.child_node_id,
        edge_label=data.edge_label,
        edge_order=data.edge_order,
    )
    db.add(edge)
    await db.flush()
    await db.refresh(edge)

    return EdgeResponse(
        id=edge.id,
        parent_node_id=edge.parent_node_id,
        child_node_id=edge.child_node_id,
        edge_label=edge.edge_label,
        edge_order=edge.edge_order,
    )


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    edge_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> None:
    """Delete an edge."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(MessagingNodeEdge)
        .options(selectinload(MessagingNodeEdge.parent_node).selectinload(MessagingNode.project))
        .where(MessagingNodeEdge.id == edge_id, MessagingNodeEdge.removed_at.is_(None))
    )
    edge = result.scalar_one_or_none()

    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    if user.role.value != "admin" and edge.parent_node.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    edge.removed_at = datetime.now(timezone.utc)
