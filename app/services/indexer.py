# app/services/indexer.py

from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.elements.primitive.paragraph import ParagraphModel
from talkingdb.models.document.indexes.index import FileIndexModel, IndexItem
from talkingdb.models.graph.graph import GraphModel
from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.clients.sqlite import sqlite_conn
from uuid import uuid4


class IndexerService:
    def __init__(self):
        self.gm = GraphModel.create(GraphModel.make_id(uuid4().hex), True)

        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()

    def graph_file_index(self, file_index: FileIndexModel) -> GraphModel:
        def walk(node: IndexItem, parent_id: str = None):
            node_id = node.id

            self.gm.graph.add_node(
                node_id,
                label=node.label,
                type=node.index,
            )

            if parent_id:
                self.gm.graph.add_edge(parent_id, node_id)

            for child in node.child:
                walk(child, node_id)

        self.gm.graph.add_node(
            file_index.id,
            label=getattr(file_index, "filename", None),
            type="file@root",
        )

        for top_node in file_index.nodes:
            walk(top_node, file_index.id)

        with sqlite_conn() as conn:
            self.gm.save(conn)

        return self.gm

    def index_document(self, document: DocumentModel) -> GraphModel:

        for element in document.iter_elements():
            if isinstance(element, ParagraphModel):
                node_id = element.id
                tokens = self.tokenizer.tokenize(element.to_text())
                symbols = self.symbol_generator.generate(tokens)

                for symbol_type, symbol_list in symbols.items():
                    for symbol in symbol_list:
                        self.gm.graph.add_node(
                            symbol,
                            type=symbol_type,
                        )
                        self.gm.graph.add_edge(node_id, symbol)

        with sqlite_conn() as conn:
            self.gm.save(conn)

        return self.gm
