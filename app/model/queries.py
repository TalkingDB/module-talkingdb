from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    graph_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of graph IDs to query against (from previous document uploads)",
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The text query to search for within the indexed documents",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return (1-100)",
    )


class MatchedNode(BaseModel):
    id: str = Field(..., description="Unique identifier of the matched node")
    graph_id: str = Field(..., description="ID of the graph containing this node")
    content: Optional[str] = Field(None, description="Text content of the node")
    type: Optional[str] = Field(None, description="Node type (e.g., 'paragraph', 'table')")
    score: float = Field(..., description="Relevance score for the match")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional node metadata")


class QueryResponse(BaseModel):
    query: str = Field(..., description="The original query text")
    graph_ids: List[str] = Field(..., description="The graph IDs that were queried")
    total_results: int = Field(..., description="Total number of matched elements returned")
    processing_time_ms: int = Field(..., description="Time taken to process the query in milliseconds")
    elements: List[MatchedNode] = Field(..., description="Matched document elements (paragraphs, tables)")
    symbols: List[MatchedNode] = Field(..., description="Matched symbols from the query tokens")
