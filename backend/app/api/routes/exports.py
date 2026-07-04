from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.exports import PeopleExportFilters
from app.services.csv_export_service import CsvExportService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("/people.csv")
async def export_people_csv(
    filters: PeopleExportFilters = Depends(),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    service = CsvExportService(db)
    csv_content = await service.export_people(filters)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="networkpilot-people-export.csv"'},
    )
