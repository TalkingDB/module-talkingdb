# app/services/extractor.py

from typing import List

from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from app.services.package_root_resolver import RootResolver
from app.services.package_semantic_extractor import SemanticExtractor


class ExtractorService:
    """
    High-level semantic extraction service.
    """

    def __init__(self):
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()
        self.root_resolver = RootResolver()
        self.semantic_extractor = SemanticExtractor()

    def extract(
        self,
        graph_id,
        query: str,
        depth: int = 2,
    ) -> List[str]:
        """
        Extract semantically related nodes for a query.
        """
        tokens = self.tokenizer.tokenize(query)
        symbols = self.symbol_generator.generate(tokens)
        resolved_symbols = self.root_resolver.resolve(symbols)

        # Flatten symbols for traversal
        query_symbols = []
        for values in resolved_symbols.values():
            query_symbols.extend(values)

        return self.semantic_extractor.extract(
            graph_id=graph_id,
            query_symbols=query_symbols,
            depth=depth,
        )
