"""Variables admin router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.variable import Variable, VariableType, VariableSourceType
from app.models.project import Project
from app.models.user import User
from app.security.deps import get_current_active_user

router = APIRouter()


class VariableCreate(BaseModel):
    """Variable creation schema."""
    project_id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    type: str = "STRING"
    source_type: str = "MANUAL"
    default_value: Optional[str] = None


class VariableUpdate(BaseModel):
    """Variable update schema."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    default_value: Optional[str] = None


class VariableResponse(BaseModel):
    """Variable response schema."""
    id: int
    project_id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    type: str
    source_type: str
    default_value: Optional[str]

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=List[VariableResponse])
async def list_variables(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> List[VariableResponse]:
    """List variables for a project."""
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
        select(Variable)
        .where(Variable.project_id == project_id, Variable.removed_at.is_(None))
        .order_by(Variable.name)
    )
    variables = result.scalars().all()

    return [
        VariableResponse(
            id=v.id,
            project_id=v.project_id,
            name=v.name,
            display_name=v.display_name,
            description=v.description,
            type=v.type.value,
            source_type=v.source_type.value,
            default_value=v.default_value,
        )
        for v in variables
    ]


@router.post("", response_model=VariableResponse, status_code=status.HTTP_201_CREATED)
async def create_variable(
    data: VariableCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> VariableResponse:
    """Create a new variable."""
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == data.project_id, Project.removed_at.is_(None))
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role.value != "admin" and project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        var_type = VariableType(data.type)
    except ValueError:
        var_type = VariableType.STRING

    try:
        source_type = VariableSourceType(data.source_type)
    except ValueError:
        source_type = VariableSourceType.MANUAL

    variable = Variable(
        project_id=data.project_id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        type=var_type,
        source_type=source_type,
        default_value=data.default_value,
    )
    db.add(variable)
    await db.flush()
    await db.refresh(variable)

    return VariableResponse(
        id=variable.id,
        project_id=variable.project_id,
        name=variable.name,
        display_name=variable.display_name,
        description=variable.description,
        type=variable.type.value,
        source_type=variable.source_type.value,
        default_value=variable.default_value,
    )


@router.get("/{variable_id}", response_model=VariableResponse)
async def get_variable(
    variable_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> VariableResponse:
    """Get a specific variable."""
    result = await db.execute(
        select(Variable)
        .options(selectinload(Variable.project))
        .where(Variable.id == variable_id, Variable.removed_at.is_(None))
    )
    variable = result.scalar_one_or_none()

    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")

    if user.role.value != "admin" and variable.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return VariableResponse(
        id=variable.id,
        project_id=variable.project_id,
        name=variable.name,
        display_name=variable.display_name,
        description=variable.description,
        type=variable.type.value,
        source_type=variable.source_type.value,
        default_value=variable.default_value,
    )


@router.put("/{variable_id}", response_model=VariableResponse)
async def update_variable(
    variable_id: int,
    data: VariableUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> VariableResponse:
    """Update a variable."""
    result = await db.execute(
        select(Variable)
        .options(selectinload(Variable.project))
        .where(Variable.id == variable_id, Variable.removed_at.is_(None))
    )
    variable = result.scalar_one_or_none()

    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")

    if user.role.value != "admin" and variable.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if data.name is not None:
        variable.name = data.name
    if data.display_name is not None:
        variable.display_name = data.display_name
    if data.description is not None:
        variable.description = data.description
    if data.type is not None:
        try:
            variable.type = VariableType(data.type)
        except ValueError:
            pass
    if data.default_value is not None:
        variable.default_value = data.default_value

    await db.flush()
    await db.refresh(variable)

    return VariableResponse(
        id=variable.id,
        project_id=variable.project_id,
        name=variable.name,
        display_name=variable.display_name,
        description=variable.description,
        type=variable.type.value,
        source_type=variable.source_type.value,
        default_value=variable.default_value,
    )


@router.delete("/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable(
    variable_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> None:
    """Delete a variable."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Variable)
        .options(selectinload(Variable.project))
        .where(Variable.id == variable_id, Variable.removed_at.is_(None))
    )
    variable = result.scalar_one_or_none()

    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")

    if user.role.value != "admin" and variable.project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    variable.removed_at = datetime.now(timezone.utc)
