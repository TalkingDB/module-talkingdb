
from fastapi import APIRouter
from app.model.index import IndexTextRequest
from app.services.indexer import IndexerService

router = APIRouter(prefix="/index", tags=["Indexer"])


@router.post("/")
async def index_text(request: IndexTextRequest):

    indexer = IndexerService()
    index = indexer.index_document(request.text)

    return index
