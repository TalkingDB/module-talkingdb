
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from talkingdb.models.metadata.metadata import DEFAULT_METADATA, Metadata
from app.model.index import IndexTextRequest
from app.services.indexer import IndexerService
from app.services.graph_html import render_graph_html
from talkingdb_ce.client import CEClient
from talkingdb.helpers.client import config

router = APIRouter(prefix="/index", tags=["Indexer"])


@router.post("/")
async def index_text(request: IndexTextRequest):

    indexer = IndexerService()
    index = indexer.index_document(request.text)

    return index.to_json()


@router.post("/document")
async def parse_file(
        document_file: UploadFile = File(None),
        metadata: Optional[str] = Form(DEFAULT_METADATA)
):
    _metadata = Metadata.from_json(metadata)
    _metadata = Metadata.ensure_metadata(_metadata)
    client = CEClient(config)
    result = client.parse_file(file=document_file, metadata=_metadata)
    return result


@router.get("/html", response_class=HTMLResponse)
async def index_text_html(text: str):
    indexer = IndexerService()
    index = indexer.index_document(text)

    html = render_graph_html(index.g_json())
    return html
