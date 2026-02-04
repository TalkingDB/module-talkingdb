
from pydantic import BaseModel


class IndexTextRequest(BaseModel):
    text: str
