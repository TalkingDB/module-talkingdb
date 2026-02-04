
from typing import Any
from pydantic import BaseModel


class ExtractTextRequest(BaseModel):
    text: str
    graph: dict