from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from app.middleware.auth import get_current_user
from app.models.user import User
from app.routes.utils import ensure_supervisor
from app.schemas.import_job import ImportJobResponse
from app.services.csv_import_service import CSVImportService
import logging
import shutil

router = APIRouter(prefix="/agents", tags=["bulk-import"])
logger = logging.getLogger(__name__)
csv_import_service = CSVImportService()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


def _save_upload(file: UploadFile) -> Path:
    """Persist the uploaded CSV to the shared uploads directory."""
    original_name = Path(file.filename or "import.csv").name
    stored_name = f"{uuid4().hex}_{original_name}"
    stored_path = UPLOAD_DIR / stored_name
    with stored_path.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)
    # Need to reset pointer for FastAPI
    file.file.seek(0)
    return stored_path


@router.post("/bulk-import", response_model=ImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv_import(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload CSV/XLSX file and start an import job. Supervisor+ only."""
    ensure_supervisor(current_user)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .csv or .xlsx file.",
        )

    stored_path = _save_upload(file)
    stored_name = stored_path.name
    try:
        job = csv_import_service.start_import_job(
            company_id=current_user.company_id,
            file_path=str(stored_path),
            file_name=stored_name,
            created_by=current_user.id,
        )
    except Exception as exc:
        if stored_path.exists():
            stored_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to create import job: {exc}") from exc

    background_tasks.add_task(csv_import_service.process_import_job, job.id)
    return job


@router.get("/bulk-import/{job_id}", response_model=ImportJobResponse)
async def get_import_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll import job status."""
    ensure_supervisor(current_user)
    job = csv_import_service.get_import_job_status(job_id)
    if not job or job.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job
