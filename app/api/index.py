
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from talkingdb.models.document.indexes.index import FileIndexModel
from talkingdb.models.graph.graph import GraphModel
from talkingdb.models.metadata.metadata import DEFAULT_METADATA, Metadata
from app.model.index import IndexTextRequest
from app.services.indexer import IndexerService
from app.services.graph_html import render_graph_html
from talkingdb.clients.sqlite import sqlite_conn
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

    indexer = IndexerService()
    index = indexer.graph_file_index(FileIndexModel(**result["file_index"]))

    return index.to_json()


@router.get("/html", response_class=HTMLResponse)
async def view_graph(graph_id: str):


    with sqlite_conn() as conn:
        gm = GraphModel.load(conn, graph_id, True)

    html = render_graph_html(gm.g_json())
    return html
