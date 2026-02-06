
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.model.index import IndexTextRequest
from app.services.indexer import IndexerService
from app.services.graph_html import render_graph_html

router = APIRouter(prefix="/index", tags=["Indexer"])


@router.post("/")
async def index_text(request: IndexTextRequest):

    indexer = IndexerService()
    index = indexer.index_document(request.text)

    return index.to_json()


@router.get("/html", response_class=HTMLResponse)
async def index_text_html(text: str):
    """
    Index text and return an interactive D3 graph HTML page.
    """
    indexer = IndexerService()
    index = indexer.index_document(text)

    html = render_graph_html(index.g_json())
    return html
