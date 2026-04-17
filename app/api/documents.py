import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from talkingdb.helpers.auth import verify_api_key
from talkingdb.helpers.client import config
from talkingdb.helpers.validation import validate_file_type, validate_file_size
from talkingdb.models.api.response import ErrorResponse
from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.indexes.index import FileIndexModel
from talkingdb.models.metadata.metadata import DEFAULT_METADATA, Metadata
from talkingdb_ce.client import CEClient

from app.model.documents import DocumentUploadResponse
from app.services.indexer import IndexerService

router = APIRouter(prefix="/v1", tags=["Documents"])


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a document",
    description=(
        "Upload a document file to be parsed, indexed, and stored as a graph structure. "
        "Currently supports .docx files. Returns the graph ID and processing metadata."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum allowed size"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal processing error"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload (.docx)"),
    metadata: Optional[str] = Form(DEFAULT_METADATA, description="JSON metadata string"),
    api_key: str = Depends(verify_api_key),
):
    ext = validate_file_type(file)
    file_size = await validate_file_size(file)

    _metadata = Metadata.from_json(metadata)
    _metadata = Metadata.ensure_metadata(_metadata)

    start = time.time()
    try:
        client = CEClient(config)
        result = await client.parse_file(file=file, metadata=_metadata)

        indexer = IndexerService()
        indexer.graph_file_index(FileIndexModel(**result["file_index"]))
        index = indexer.index_document(DocumentModel.from_dict(result["document"]))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "PROCESSING_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PROCESSING_ERROR",
                "message": f"Failed to process document: {type(e).__name__}",
            },
        )

    processing_time_ms = int((time.time() - start) * 1000)

    return DocumentUploadResponse(
        graph_id=index.graph_id,
        filename=file.filename,
        file_type=ext,
        file_size_bytes=file_size,
        processing_time_ms=processing_time_ms,
        created_at=datetime.now(timezone.utc),
    )
