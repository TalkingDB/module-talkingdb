# app/services/indexer.py

from typing import List

from app.services.package_content_elementizer import ContentElementizer, ContentElement
from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from app.services.package_root_resolver import RootResolver
from app.services.package_graph_indexer import GraphIndexer
from networkx.readwrite import json_graph


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

        return {
            "elements_indexed": len(elements),
            "graph": json_graph.node_link_data(self.graph_indexer.graph),
        }
