
from fastapi import APIRouter
from app.model.extract import ExtractTextRequest
from app.services.extractor import ExtractorService

router = APIRouter(prefix="/extract", tags=["Extractor"])


@router.post("")
async def extract_nodes(request: ExtractTextRequest):

    extractor = ExtractorService(graph_ids=request.graph_ids)
    nodes = extractor.extract(query=request.text)

    return nodes
