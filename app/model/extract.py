
from typing import Any, List
from pydantic import BaseModel


class ExtractTextRequest(BaseModel):
    graph_ids: List[str]
    text: str
