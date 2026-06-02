from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.job import store as job_store
from talkingdb.models.api.response import ErrorResponse
from talkingdb.models.job.job import JobModel

from app.model.jobs import JobStatusResponse


router = APIRouter(prefix="/v1", tags=["Jobs"])


def _no_store(response: Response) -> None:
    """Prevent proxies / browsers / gateways from caching job status."""
    response.headers["Cache-Control"] = "no-store"


def _job_or_404(job_id: str) -> JobModel:
    """Return a persisted job or raise HTTP 404."""
    with sqlite_conn() as conn:
        job = job_store.get(conn, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "JOB_NOT_FOUND",
                "message": f"Unknown job id: {job_id}",
            },
        )
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get current status of a job",
    description=(
        "Return the current lifecycle state and progress of a job. "
        "The ``job_type`` field tells the caller what kind of background "
        "operation this job represents."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Unknown job id"},
    },
)
async def get_job_status(
    response: Response,
    job_id: str = Path(..., description="Stable job identifier"),
    api_key: str = Depends(verify_api_key),
) -> JobStatusResponse:
    """Fetch the latest persisted state for a job."""
    _no_store(response)
    job = _job_or_404(job_id)
    return JobStatusResponse(**job.to_status_payload())


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=JobStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request cancellation of a job",
    description=(
        "Request cooperative cancellation of a queued or running job. "
        "Idempotent: cancelling a terminal job echoes the same terminal state."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Unknown job id"},
    },
)
async def cancel_job(
    response: Response,
    job_id: str = Path(..., description="Stable job identifier"),
    api_key: str = Depends(verify_api_key),
) -> JobStatusResponse:
    """Request cancellation for a queued or running job."""
    _no_store(response)
    _job_or_404(job_id)
    with sqlite_conn() as conn:
        updated = job_store.request_cancel(conn, job_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="vanished"
        )
    return JobStatusResponse(**updated.to_status_payload())
