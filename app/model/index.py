

from pydantic import BaseModel

from talkingdb.models.document.document import DocumentModel
from talkingdb.models.metadata.metadata import Metadata


class IndexElementRequest(BaseModel):
    metadata: Metadata
    document: DocumentModel
