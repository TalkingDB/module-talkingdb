# app/services/indexer.py

from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.elements.primitive.paragraph import ParagraphModel
from talkingdb.models.document.elements.primitive.table import TableModel
from talkingdb.models.document.indexes.index import FileIndexModel, IndexItem, IndexType
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

                heading_path = document._get_heading_path(element)

                metadata = {
                    "index": IndexType.PARA,
                    "heading_path": heading_path,
                    "filename": document.filename
                }

                self.gm.graph.add_node(
                    node_id, text=text, metadata=metadata, type="paragraph")

                for symbol_type, symbol_list in symbols.items():
                    for symbol in symbol_list:
                        self.gm.graph.add_node(
                            symbol,
                            type=symbol_type,
                        )
                        self.gm.graph.add_edge(
                            node_id, symbol, type="contains")

                # TODO: extract key pairs from elements
                for line in text.splitlines():
                    line = line.strip()
                    if ":" not in line:
                        continue

                    key_raw, val_raw = [part.strip()
                                        for part in line.split(":", 1)]
                    if not key_raw or not val_raw:
                        continue

                    key_id = self.symbol_generator.max_gram(
                        self.tokenizer.tokenize(key_raw))
                    val_id = self.symbol_generator.max_gram(
                        self.tokenizer.tokenize(val_raw, False))

                    self.gm.graph.add_node(key_id, text=key_raw, is_key=True)
                    self.gm.graph.add_node(val_id, text=val_raw, is_val=True)
                    self.gm.graph.add_edge(key_id, val_id, type="key_value")

                    self.gm.graph.add_edge(node_id, key_id, type="contains")
                    self.gm.graph.add_edge(node_id, val_id, type="describes")

            if isinstance(element, TableModel):
                node_id = element.caption_ref_id or element.id
                caption_elem = document.get_element_by_id(element.caption_ref_id)
                table_caption = [caption_elem.to_text()] if caption_elem else []

                text = element.to_html()
                heading_path = document._get_heading_path(element) + table_caption

                metadata = {
                    "index": IndexType.TABLE,
                    "heading_path": heading_path,
                    "filename": document.filename
                }

                self.gm.graph.add_node(
                    node_id, text=text, metadata=metadata, type="table")

                
                for row_idx, row in enumerate(element.rows):
                    for col_idx, cell in enumerate(row):
                        header = ", ".join(element.get_header(row_idx, col_idx))
                        header_tokens = self.tokenizer.tokenize(header, False)
                        header_symbols = self.symbol_generator.generate(header_tokens)

                        metadata = {
                            "index": IndexType.TABLE_HEADER,
                            "heading_path": heading_path,
                            "filename": document.filename
                        }

                        self.gm.graph.add_node(
                            header, text=header, metadata=metadata, type="header")
                        self.gm.graph.add_edge(
                            node_id, header, type="part_of")

                        for symbol_type, symbol_list in header_symbols.items():
                            for symbol in symbol_list:
                                self.gm.graph.add_node(
                                    symbol,
                                    type=symbol_type,
                                )
                                self.gm.graph.add_edge(
                                    header, symbol, type="contains")
                        
                        cell_text = cell.to_text()

                        cell_tokens = self.tokenizer.tokenize(cell_text)
                        cell_symbols = self.symbol_generator.generate(cell_tokens)

                        for symbol_type, symbol_list in cell_symbols.items():
                            for symbol in symbol_list:
                                self.gm.graph.add_node(
                                    symbol,
                                    type=symbol_type,
                                )
                                self.gm.graph.add_edge(
                                    header, symbol, type="contains")
                        
                        key_id = self.symbol_generator.max_gram(
                            self.tokenizer.tokenize(header, False))
                        val_id = self.symbol_generator.max_gram(
                            self.tokenizer.tokenize(cell_text, False))

                        self.gm.graph.add_node(key_id, text=key_raw, is_key=True)
                        self.gm.graph.add_node(val_id, text=val_raw, is_val=True)
                        self.gm.graph.add_edge(key_id, val_id, type="key_value")


        with sqlite_conn() as conn:
            self.gm.save(conn)

        self.gm.clear()
        
        return self.gm
