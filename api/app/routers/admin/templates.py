"""Templates admin router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.message_template import MessageTemplate, MessageTemplateText
from app.models.project import Project
from app.models.user import User
from app.security.deps import get_current_active_user

router = APIRouter()


class TemplateTextCreate(BaseModel):
    """Template text creation schema."""
    language_id: int
    message_text: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    quick_replies: List[dict] = []


class TemplateCreate(BaseModel):
    """Template creation schema."""
    project_id: int
    name: str
    description: Optional[str] = None
    type: str = "STANDARD"
    texts: List[TemplateTextCreate] = []


class TemplateTextResponse(BaseModel):
    """Template text response schema."""
    id: int
    language_id: int
    message_text: Optional[str]
    media_url: Optional[str]
    media_type: Optional[str]
    quick_replies: List[dict]

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Template response schema."""
    id: int
    project_id: int
    name: str
    description: Optional[str]
    type: str
    texts: List[TemplateTextResponse] = []

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=List[TemplateResponse])
async def list_templates(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> List[TemplateResponse]:
    """List templates for a project.

    Args:
        project_id: Project ID
        db: Database session
        user: Current user

    Returns:
        List of templates
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
        select(MessageTemplate)
        .options(selectinload(MessageTemplate.texts))
        .where(
            MessageTemplate.project_id == project_id,
            MessageTemplate.removed_at.is_(None),
        )
        .order_by(MessageTemplate.name)
    )
    templates = result.scalars().all()

    return [
        TemplateResponse(
            id=t.id,
            project_id=t.project_id,
            name=t.name,
            description=t.description,
            type=t.type,
            texts=[
                TemplateTextResponse(
                    id=txt.id,
                    language_id=txt.language_id,
                    message_text=txt.message_text,
                    media_url=txt.media_url,
                    media_type=txt.media_type,
                    quick_replies=txt.quick_replies or [],
                )
                for txt in t.texts
            ],
        )
        for t in templates
    ]


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> TemplateResponse:
    """Create a new message template.

    Args:
        data: Template data
        db: Database session
        user: Current user

    Returns:
        Created template
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

    template = MessageTemplate(
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        type=data.type,
    )
    db.add(template)
    await db.flush()

    # Add texts
    for text_data in data.texts:
        text = MessageTemplateText(
            template_id=template.id,
            language_id=text_data.language_id,
            message_text=text_data.message_text,
            media_url=text_data.media_url,
            media_type=text_data.media_type,
            quick_replies=text_data.quick_replies,
        )
        db.add(text)

    await db.flush()
    await db.refresh(template)

    # Reload with texts
    result = await db.execute(
        select(MessageTemplate)
        .options(selectinload(MessageTemplate.texts))
        .where(MessageTemplate.id == template.id)
    )
    template = result.scalar_one()

    return TemplateResponse(
        id=template.id,
        project_id=template.project_id,
        name=template.name,
        description=template.description,
        type=template.type,
        texts=[
            TemplateTextResponse(
                id=txt.id,
                language_id=txt.language_id,
                message_text=txt.message_text,
                media_url=txt.media_url,
                media_type=txt.media_type,
                quick_replies=txt.quick_replies or [],
            )
            for txt in template.texts
        ],
    )


class TemplateUpdate(BaseModel):
    """Template update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    texts: Optional[List[TemplateTextCreate]] = None


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> TemplateResponse:
    """Update a message template."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(MessageTemplate)
        .options(
            selectinload(MessageTemplate.texts),
            selectinload(MessageTemplate.project),
        )
        .where(MessageTemplate.id == template_id, MessageTemplate.removed_at.is_(None))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if user.role.value != "admin" and template.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.type is not None:
        template.type = data.type

    # Replace texts if provided
    if data.texts is not None:
        # Soft-delete existing texts
        for existing_text in template.texts:
            existing_text.removed_at = datetime.now(timezone.utc)

        # Add new texts
        for text_data in data.texts:
            text = MessageTemplateText(
                template_id=template.id,
                language_id=text_data.language_id,
                message_text=text_data.message_text,
                media_url=text_data.media_url,
                media_type=text_data.media_type,
                quick_replies=text_data.quick_replies,
            )
            db.add(text)

    await db.flush()

    # Reload with fresh texts
    result = await db.execute(
        select(MessageTemplate)
        .options(selectinload(MessageTemplate.texts))
        .where(MessageTemplate.id == template.id)
    )
    template = result.scalar_one()

    return TemplateResponse(
        id=template.id,
        project_id=template.project_id,
        name=template.name,
        description=template.description,
        type=template.type,
        texts=[
            TemplateTextResponse(
                id=txt.id,
                language_id=txt.language_id,
                message_text=txt.message_text,
                media_url=txt.media_url,
                media_type=txt.media_type,
                quick_replies=txt.quick_replies or [],
            )
            for txt in template.texts
            if txt.removed_at is None
        ],
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> TemplateResponse:
    """Get a specific template.

    Args:
        template_id: Template ID
        db: Database session
        user: Current user

    Returns:
        Template details
    """
    result = await db.execute(
        select(MessageTemplate)
        .options(
            selectinload(MessageTemplate.texts),
            selectinload(MessageTemplate.project),
        )
        .where(MessageTemplate.id == template_id, MessageTemplate.removed_at.is_(None))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if user.role.value != "admin" and template.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TemplateResponse(
        id=template.id,
        project_id=template.project_id,
        name=template.name,
        description=template.description,
        type=template.type,
        texts=[
            TemplateTextResponse(
                id=txt.id,
                language_id=txt.language_id,
                message_text=txt.message_text,
                media_url=txt.media_url,
                media_type=txt.media_type,
                quick_replies=txt.quick_replies or [],
            )
            for txt in template.texts
        ],
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> None:
    """Delete a template.

    Args:
        template_id: Template ID
        db: Database session
        user: Current user
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(MessageTemplate)
        .options(selectinload(MessageTemplate.project))
        .where(MessageTemplate.id == template_id, MessageTemplate.removed_at.is_(None))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if user.role.value != "admin" and template.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    template.removed_at = datetime.now(timezone.utc)
