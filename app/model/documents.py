from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    graph_id: str = Field(..., description="Unique identifier for the indexed document graph")
    filename: str = Field(..., description="Original filename of the uploaded document")
    file_type: str = Field(..., description="Detected file type (e.g., 'docx')")
    file_size_bytes: int = Field(..., description="Size of the uploaded file in bytes")
    processing_time_ms: int = Field(..., description="Time taken to process the document in milliseconds")
    created_at: datetime = Field(..., description="Timestamp when the document was indexed")
