import logging
import traceback
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas import ManualChunkRead, ManualRead
from app.services.rag import RagService

router = APIRouter(prefix="/api/manuals", tags=["manuals"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=ManualRead)
async def upload_manual(
    file: UploadFile = File(...),
    code: str | None = Form(default=None),
    title: str | None = Form(default=None),
    rule_code: str | None = Form(default="R-ELV-CABLE-001"),
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())
    file_name = file.filename or "manual.txt"
    try:
        content = await file.read()
        return RagService(db).create_uploaded_manual(
            file_name=file_name,
            content=content,
            code=code,
            title=title,
            rule_code=rule_code,
        )
    except Exception as exc:
        db.rollback()
        trace = traceback.format_exc()
        logger.exception(
            "Manual upload failed request_id=%s file_name=%s code=%s title=%s",
            request_id,
            file_name,
            code,
            title,
        )
        detail = {
            "request_id": request_id,
            "error": "manual_upload_failed",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "log": f"Manual upload failed request_id={request_id} file_name={file_name}",
        }
        if get_settings().environment != "production":
            detail["traceback"] = trace
        return JSONResponse(status_code=500, content=detail)


@router.get("", response_model=list[ManualRead])
def list_manuals(db: Session = Depends(get_db)):
    return RagService(db).list_manuals()


@router.get("/{manual_id}", response_model=ManualRead)
def get_manual(manual_id: str, db: Session = Depends(get_db)):
    manual = RagService(db).get_manual(manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found")
    return manual


@router.post("/{manual_id}/parse", response_model=list[ManualChunkRead])
def parse_manual(manual_id: str, db: Session = Depends(get_db)):
    service = RagService(db)
    manual = service.get_manual(manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found")
    return service.parse_manual(manual)


@router.get("/{manual_id}/chunks", response_model=list[ManualChunkRead])
def list_manual_chunks(manual_id: str, db: Session = Depends(get_db)):
    service = RagService(db)
    if not service.get_manual(manual_id):
        raise HTTPException(status_code=404, detail="Manual not found")
    return service.list_chunks(manual_id)
