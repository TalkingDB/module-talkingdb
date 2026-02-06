
from typing import Any
from pydantic import BaseModel


class ExtractTextRequest(BaseModel):
    graph_id: str
    text: str
