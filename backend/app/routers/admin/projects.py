"""Projects admin router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.participant import Participant
from app.models.messaging_node import MessagingNode
from app.models.user import User
from app.security.deps import get_current_active_user, require_researcher_or_admin

router = APIRouter()


class ProjectCreate(BaseModel):
    """Project creation schema."""
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Project update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema."""
    id: int
    uu_id: Optional[str]
    name: str
    description: Optional[str]
    status: str
    owner_id: int
    owner_email: str
    participant_count: int = 0
    node_count: int = 0

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Paginated project list response."""
    items: List[ProjectResponse]
    total: int
    page: int
    size: int


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = 1,
    size: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ProjectListResponse:
    """List all projects accessible to the user.

    Args:
        page: Page number (1-indexed)
        size: Page size
        status_filter: Optional status filter
        db: Database session
        user: Current user

    Returns:
        Paginated list of projects
    """
    # Subqueries for counts (avoid lazy loading in async context)
    participant_count_subq = (
        select(func.count(Participant.id))
        .where(Participant.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )
    node_count_subq = (
        select(func.count(MessagingNode.id))
        .where(MessagingNode.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )

    query = (
        select(
            Project,
            participant_count_subq.label("participant_count"),
            node_count_subq.label("node_count"),
        )
        .options(selectinload(Project.owner))
        .where(Project.removed_at.is_(None))
    )

    # Filter by status if provided
    if status_filter:
        try:
            status_enum = ProjectStatus(status_filter)
            query = query.where(Project.status == status_enum)
        except ValueError:
            pass

    # Non-admin users only see their own projects or projects they have access to
    if user.role.value != "admin":
        query = query.where(Project.user_id == user.id)

    # Count total
    count_result = await db.execute(select(Project.id).where(Project.removed_at.is_(None)))
    total = len(count_result.all())

    # Paginate
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Project.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    items = [
        ProjectResponse(
            id=p.id,
            uu_id=p.uu_id,
            name=p.name,
            description=p.description,
            status=p.status.value,
            owner_id=p.user_id,
            owner_email=p.owner.email if p.owner else "",
            participant_count=participant_count or 0,
            node_count=node_count or 0,
        )
        for p, participant_count, node_count in rows
    ]

    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> ProjectResponse:
    """Create a new project.

    Args:
        data: Project creation data
        db: Database session
        user: Current user (researcher or admin)

    Returns:
        Created project
    """
    project = Project(
        name=data.name,
        description=data.description,
        user_id=user.id,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        uu_id=project.uu_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        owner_id=project.user_id,
        owner_email=user.email,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Get a specific project by ID.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Project details

    Raises:
        HTTPException: If project not found or not accessible
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.owner))
        .where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ProjectResponse(
        id=project.id,
        uu_id=project.uu_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        owner_id=project.user_id,
        owner_email=project.owner.email if project.owner else "",
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> ProjectResponse:
    """Update a project.

    Args:
        project_id: Project ID
        data: Update data
        db: Database session
        user: Current user

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or not accessible
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.owner))
        .where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update fields
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        try:
            project.status = ProjectStatus(data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {data.status}",
            )

    await db.flush()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        uu_id=project.uu_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        owner_id=project.user_id,
        owner_email=project.owner.email if project.owner else "",
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> None:
    """Soft-delete a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Raises:
        HTTPException: If project not found or not accessible
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    project.removed_at = datetime.now(timezone.utc)
    project.status = ProjectStatus.DELETED


@router.post("/{project_id}/activate", response_model=ProjectResponse)
async def activate_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> ProjectResponse:
    """Activate a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Updated project
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.owner))
        .where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    project.status = ProjectStatus.ACTIVE
    await db.flush()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        uu_id=project.uu_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        owner_id=project.user_id,
        owner_email=project.owner.email if project.owner else "",
    )


@router.post("/{project_id}/suspend", response_model=ProjectResponse)
async def suspend_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_researcher_or_admin),
) -> ProjectResponse:
    """Suspend a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        Updated project
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.owner))
        .where(Project.id == project_id, Project.removed_at.is_(None))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    project.status = ProjectStatus.SUSPENDED
    await db.flush()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        uu_id=project.uu_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        owner_id=project.user_id,
        owner_email=project.owner.email if project.owner else "",
    )
