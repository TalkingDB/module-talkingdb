
from fastapi import APIRouter
from app.model.extract import ExtractTextRequest
from app.services.extractor import ExtractorService
from networkx.readwrite import json_graph

router = APIRouter(prefix="/extract", tags=["Extractor"])


@router.post("/")
async def extract_nodes(request: ExtractTextRequest):

    extractor = ExtractorService()
    nodes = extractor.extract(
        graph=json_graph.node_link_graph(request.graph),
        query=request.text,
        depth=2,
    )

    return nodes
