"""Admin router - /v1/admin/*."""

from fastapi import APIRouter

from app.routers.admin import (
    projects, participants, templates, nodes, variables,
    analytics, testing, protocol_test, protocol_import,
)

router = APIRouter()

# Include sub-routers
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(participants.router, prefix="/participants", tags=["Participants"])
router.include_router(templates.router, prefix="/templates", tags=["Templates"])
router.include_router(nodes.router, prefix="/nodes", tags=["Nodes"])
router.include_router(variables.router, prefix="/variables", tags=["Variables"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(testing.router, prefix="/testing", tags=["Testing"])
router.include_router(protocol_test.router, prefix="/protocol-test", tags=["Protocol Testing"])
router.include_router(protocol_import.router, prefix="/protocol", tags=["Protocol Import/Export"])
