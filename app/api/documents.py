from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers import spool
from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.job import store as job_store
from talkingdb.helpers.validation import (
    validate_file_type,
    max_file_size_bytes_for,
    max_file_size_mb_for,
)
from talkingdb.models.api.response import ErrorResponse
from talkingdb.models.job.job import JobModel
from talkingdb.models.job.type import JobType
from talkingdb.models.metadata.metadata import DEFAULT_METADATA

from app.core import config as job_config
from app.model.jobs import JobAcceptedResponse
from app.services import jobs


router = APIRouter(prefix="/v1", tags=["Jobs"])


@router.post(
    "/documents",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a document for asynchronous indexing",
    description=(
        "Upload a document for asynchronous indexing. Returns immediately "
        "with a stable ``job_id`` that can be polled at "
        "``GET /v1/jobs/{job_id}`` and cancelled at "
        "``POST /v1/jobs/{job_id}/cancel``."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum allowed size"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        429: {"model": ErrorResponse, "description": "Worker queue is full"},
        503: {"model": ErrorResponse, "description": "Spool storage exhausted"},
    },
)
async def submit_document_job(
    file: UploadFile = File(..., description="The document file to upload (.docx or .pdf)"),
    metadata: Optional[str] = Form(DEFAULT_METADATA, description="JSON metadata string"),
    api_key: str = Depends(verify_api_key),
) -> JobAcceptedResponse:
    """Submit a document ingestion job for background processing."""
    ext = validate_file_type(file)

    spool.assert_spool_capacity()

    try:
        jobs.acquire_slot()
    except jobs.QueueFull:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "QUEUE_FULL",
                "error_code": "QUEUE_FULL",
                "message": "Ingestion worker pool is at capacity",
                "retry_after_seconds": job_config.RETRY_AFTER_SECONDS,
            },
            headers={"Retry-After": str(job_config.RETRY_AFTER_SECONDS)},
        )

    temp_path: Optional[str] = None
    enqueued = False
    try:
        temp_path, size_bytes = await spool.spool_upload(
            file,
            max_size_mb=max_file_size_mb_for(ext),
            max_size_bytes=max_file_size_bytes_for(ext),
        )

        metadata_json = metadata if metadata else DEFAULT_METADATA

        job = JobModel.new(
            job_type=JobType.DOCUMENT,
            filename=file.filename,
        )
        job.file_size_bytes = size_bytes
        job.temp_path = temp_path

        with sqlite_conn() as conn:
            job_store.insert(conn, job)

        jobs.enqueue_reserved(
            job_id=job.job_id,
            temp_path=temp_path,
            filename=file.filename or f"upload.{ext}",
            metadata_json=metadata_json,
        )
        enqueued = True

        return JobAcceptedResponse(
            job_id=job.job_id,
            job_type=job.job_type.value,
            state=job.state.value,
        )

    finally:
        if not enqueued:
            spool.discard(temp_path)
            jobs.release_slot()
