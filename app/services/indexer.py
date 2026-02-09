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
                index=node.index,
            )

            if parent_id:
                self.gm.graph.add_edge(parent_id, node_id, type="part_of")

            for child in node.child:
                walk(child, node_id)

        self.gm.graph.add_node(
            file_index.id,
            label=getattr(file_index, "filename", None),
            index="file@root",
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
                text = element.to_text()

                tokens = self.tokenizer.tokenize(text)
                symbols = self.symbol_generator.generate(tokens)

                self.gm.graph.add_node(node_id, text=text, type="element")

                for symbol_type, symbol_list in symbols.items():
                    for symbol in symbol_list:
                        self.gm.graph.add_node(
                            symbol,
                            type=symbol_type,
                        )
                        self.gm.graph.add_edge(node_id, symbol, type="contains")

                # TODO: extract key pairs from elements
                for line in text.splitlines():
                    line = line.strip()
                    if ":" not in line:
                        continue

                    key_raw, val_raw = [part.strip() for part in line.split(":", 1)]
                    if not key_raw or not val_raw:
                        continue

                    key_id = self.symbol_generator.max_gram(self.tokenizer.tokenize(key_raw))
                    val_id = self.symbol_generator.max_gram(self.tokenizer.tokenize(val_raw, False))
                    
                    self.gm.graph.add_node(key_id, text=key_raw, is_key=True)
                    self.gm.graph.add_node(val_id, text=val_raw, is_val=True)
                    self.gm.graph.add_edge(key_id, val_id, type="key_value")

                    self.gm.graph.add_edge(node_id, key_id, type="contains")
                    self.gm.graph.add_edge(node_id, val_id, type="describes")

        with sqlite_conn() as conn:
            self.gm.save(conn)

        return self.gm
