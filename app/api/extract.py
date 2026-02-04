
from fastapi import APIRouter
from app.model.extract import ExtractTextRequest

router = APIRouter(prefix="/extract", tags=["Extractor"])


@router.post("/")
async def extract_nodes(request: ExtractTextRequest):
    text = request.text
    index_id = request.index_id
    # TODO
    # Here you would add the logic to extract the text
    extract_nodes = "extract_nodes"

    return extract_nodes
