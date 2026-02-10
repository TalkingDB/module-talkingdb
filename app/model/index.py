

from pydantic import BaseModel

from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.indexes.index import FileIndexModel
from talkingdb.models.metadata.metadata import Metadata


class IndexElementRequest(BaseModel):
    metadata: Metadata
    document: DocumentModel
    file_index: FileIndexModel
