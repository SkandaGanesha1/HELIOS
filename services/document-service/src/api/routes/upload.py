"""Document upload and extraction API routes"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pathlib import Path
import uuid
import aiofiles
from typing import Dict, Any

from ...database.jobs import create_job, get_job, update_job_status, list_jobs
from ...workflows.langgraph_extraction import run_extraction_workflow
from ...config import settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    Upload a loan document for extraction.

    Supports: PDF, DOCX (max 50MB)
    Returns: job_id for tracking
    """

    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size (convert MB to bytes)
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create job record
    await create_job(
        job_id=job_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        status="pending"
    )

    # Trigger background extraction
    background_tasks.add_task(
        run_extraction_workflow,
        job_id=job_id,
        file_path=str(file_path)
    )

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document uploaded successfully. Extraction started."
    }

@router.get("/{job_id}/status")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get extraction job status and results"""
    job = await get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "filename": job["filename"],
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"] if job["status"] == "completed" else None,
        "error": job["error"] if job["status"] == "failed" else None,
        "confidence": job["confidence"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"]
    }

@router.get("/")
async def list_all_jobs(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List all extraction jobs with pagination"""
    jobs = await list_jobs(limit=limit, offset=offset)

    return {
        "total": len(jobs),
        "limit": limit,
        "offset": offset,
        "jobs": jobs
    }

@router.delete("/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Delete a job and its uploaded file"""
    job = await get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete uploaded file
    file_path = Path(job["file_path"])
    if file_path.exists():
        file_path.unlink()

    # In a real implementation, delete from database
    # For now, just mark as deleted
    await update_job_status(job_id, status="deleted")

    return {"message": f"Job {job_id} deleted successfully"}
