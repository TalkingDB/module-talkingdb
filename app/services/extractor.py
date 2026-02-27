# app/services/extractor.py

from typing import Dict, List
from collections import Counter

from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.helpers.graph_cache import graph_cache


class ExtractorService:

    def __init__(self, graph_id: str, max_matches: int = 10):
        self.gm = graph_cache.get(graph_id)

        self.max_matches = max_matches
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()

    # ─────────────────────────────────────────────────────────────
    # Public API (NO GRAPH MUTATION)
    # ─────────────────────────────────────────────────────────────

    def extract(self, query: str):

        tokens = self.tokenizer.tokenize(query)
        symbols = self.symbol_generator.generate(tokens)

        # Try trigram → bigram → unigram
        for symbol_type in self.symbol_generator.grams():

            elements, matched_symbols = self._collect_paragraphs(
                symbols.get(symbol_type, []),
                symbol_type
            )

            if elements:
                return self.get_scores(matched_symbols, elements)

        return self.get_scores({}, {})

    # ─────────────────────────────────────────────────────────────
    # Core Traversal (NO QUERY NODE)
    # ─────────────────────────────────────────────────────────────

    def _collect_paragraphs(
        self,
        query_symbols: List[str],
        symbol_type: str,
    ):

        symbols_counter = Counter()
        elements_counter = Counter()

        graph = self.gm.graph

        for symbol in query_symbols:

            if symbol not in graph:
                continue

            if graph.nodes[symbol].get("type") != symbol_type:
                continue

            for neighbor in graph.neighbors(symbol):
                node_type = graph.nodes[neighbor].get("type")

                if node_type not in ("paragraph", "table"):
                    continue

                elements_counter[neighbor] += 1
                symbols_counter[symbol] += 1

        return elements_counter, symbols_counter

    # ─────────────────────────────────────────────────────────────
    # Ranking (UNCHANGED)
    # ─────────────────────────────────────────────────────────────

    def get_scores(
        self,
        symbol_scores: Dict[str, float],
        element_scores: Dict[str, float],
    ):

        def score_key(item):
            return (-round(item[1], 6), item[0])

        ranked_symbols = sorted(symbol_scores.items(), key=score_key)
        ranked_elements = sorted(element_scores.items(), key=score_key)

        if self.max_matches and self.max_matches > 0:
            ranked_symbols = ranked_symbols[: self.max_matches]
            ranked_elements = ranked_elements[: self.max_matches]

        matched_symbols = []
        matched_elements = []

        graph = self.gm.graph

        for symbol, score in ranked_symbols:
            matched_symbols.append({
                "id": symbol,
                "content": graph.nodes[symbol].get("text"),
                "type": graph.nodes[symbol].get("type"),
                "score": score,
            })

        for element, score in ranked_elements:
            matched_elements.append({
                "id": element,
                "content": graph.nodes[element].get("text"),
                "type": graph.nodes[element].get("type"),
                "metadata": graph.nodes[element].get("metadata"),
                "score": score,
            })

        return {
            "elements": matched_elements,
            "symbols": matched_symbols,
        }