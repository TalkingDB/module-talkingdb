# app/services/indexer.py

from typing import List
import networkx as nx
from talkingdb.models.document.indexes.index import FileIndexModel, IndexItem
from talkingdb.models.graph.graph import GraphModel
from app.services.package_content_elementizer import ContentElementizer, ContentElement
from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from app.services.package_root_resolver import RootResolver
from app.services.package_graph_indexer import GraphIndexer
from talkingdb.clients.sqlite import sqlite_conn
from uuid import uuid4


class IndexerService:
    """
    High-level indexing orchestration service.
    """

    def __init__(self):
        self.elementizer = ContentElementizer()
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()
        self.root_resolver = RootResolver()
        self.graph_indexer = GraphIndexer()

    def index_document(self, content: str):
        """
        Index a document into the semantic graph.
        """
        elements: List[ContentElement] = self.elementizer.elementize(content)

        for element in elements:
            tokens = self.tokenizer.tokenize(element.text)
            symbols = self.symbol_generator.generate(tokens)
            resolved_symbols = self.root_resolver.resolve(symbols)

            self.graph_indexer.index(
                element_id=element.id,
                symbols=resolved_symbols,
            )
        gm = GraphModel(
            graph_id=GraphModel.make_id(uuid4().hex),
            graph=self.graph_indexer.graph,
        )
        with sqlite_conn() as conn:
            gm.save(conn)

        return gm

    def graph_file_index(self, file_index: FileIndexModel) -> GraphModel:
        graph = nx.DiGraph()

        def walk(node: IndexItem, parent_id: str = None):
            node_id = node.id

            graph.add_node(
                node_id,
                label=node.label,
                index=node.index,
            )

            if parent_id:
                graph.add_edge(parent_id, node_id)

            for child in node.child:
                walk(child, node_id)

        graph.add_node(
            file_index.id,
            label=getattr(file_index, "filename", None),
            index="file@root",
        )

        for top_node in file_index.nodes:
            walk(top_node, file_index.id)

        gm = GraphModel(
            graph_id=GraphModel.make_id(uuid4().hex),
            graph=graph,
        )

        with sqlite_conn() as conn:
            gm.save(conn)

        return gm
