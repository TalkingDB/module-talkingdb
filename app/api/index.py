
from fastapi import APIRouter
from app.model.index import IndexTextRequest

router = APIRouter(prefix="/index", tags=["Indexer"])


@router.post("/")
async def index_text(request: IndexTextRequest):
    text = request.text
    # TODO
    # Here you would add the logic to index the text
    index_id = "index_id"

    return index_id
