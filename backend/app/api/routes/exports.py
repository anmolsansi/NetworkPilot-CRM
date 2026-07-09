import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger, mask_id
from app.schemas.exports import PeopleExportFilters
from app.services.csv_export_service import CsvExportService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("/people.csv")
async def export_people_csv(
    filters: PeopleExportFilters = Depends(),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "exports.people_csv.started workspace_id=%s include_private_notes=%s",
        mask_id(str(filters.workspace_id)),
        filters.include_private_notes,
    )
    service = CsvExportService(db)
    csv_content = await service.export_people(filters)
    logger.info(
        "exports.people_csv.completed workspace_id=%s byte_size=%s",
        mask_id(str(filters.workspace_id)),
        len(csv_content.encode("utf-8")),
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="networkpilot-people-export.csv"'},
    )
