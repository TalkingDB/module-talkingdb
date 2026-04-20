import time

from fastapi import APIRouter, Depends, HTTPException, status

from talkingdb.helpers.auth import verify_api_key
from talkingdb.models.api.response import ErrorResponse

from app.model.queries import QueryRequest, QueryResponse
from app.services.extractor import ExtractorService

router = APIRouter(prefix="/v1", tags=["Queries"])


@router.post(
    "/queries",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query indexed documents",
    description=(
        "Submit a text query against one or more previously indexed document graphs. "
        "Returns matched elements (paragraphs, tables) and symbols ranked by relevance."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "One or more graph IDs not found"},
        422: {"model": ErrorResponse, "description": "Validation error in request payload"},
        500: {"model": ErrorResponse, "description": "Internal query processing error"},
    },
)
async def query_documents(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key),
):
    start = time.time()

    try:
        extractor = ExtractorService(
            graph_ids=request.graph_ids,
            max_matches=request.max_results,
        )
        result = extractor.extract(query=request.text)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "GRAPH_NOT_FOUND",
                "message": f"Graph ID not found: {str(e)}",
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "GRAPH_NOT_FOUND",
                "message": f"One or more graph IDs could not be loaded: {str(e)}",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "QUERY_ERROR",
                "message": f"Failed to process query: {type(e).__name__}",
            },
        )

    processing_time_ms = int((time.time() - start) * 1000)

    elements = result.get("elements", [])
    symbols = result.get("symbols", [])

    return QueryResponse(
        query=request.text,
        graph_ids=request.graph_ids,
        total_results=len(elements),
        processing_time_ms=processing_time_ms,
        elements=elements,
        symbols=symbols,
    )
