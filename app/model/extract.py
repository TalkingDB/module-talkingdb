
from pydantic import BaseModel


class ExtractTextRequest(BaseModel):
    text: str
    index_id: str
