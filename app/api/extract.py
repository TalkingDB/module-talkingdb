
from fastapi import APIRouter
from app.model.extract import ExtractTextRequest
from app.services.extractor import ExtractorService

router = APIRouter(prefix="/extract", tags=["Extractor"])


@router.post("/")
async def extract_nodes(request: ExtractTextRequest):

    extractor = ExtractorService()

    nodes = extractor.extract(
        graph_id=request.graph_id,
        query=request.text,
        depth=2,
    )

    return nodes
