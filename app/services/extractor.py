# app/services/extractor.py

import math
from typing import Dict, List, Set
from uuid import uuid4

from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.helpers.graph_cache import graph_cache
from collections import Counter

NGRAM_WEIGHTS: Dict[str, int] = {
    "trigram": 3,
    "bigram": 2,
    "unigram": 1,
}

PARTIAL_FACTOR: float = 0.4

EDGE_WEIGHTS: Dict[str, float] = {
    "contains": 1.0,
    "describes": 1.2,
}

MAX_EDGE_CONTRIBUTION: int = 10


class ExtractorService:

    def __init__(self, graph_id: str, max_matches: int = 10):
        self.gm = graph_cache.get(graph_id)

        self.max_matches = max_matches
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()

        self._unigram_index: Dict[str, Set[str]] = {}

    def _build_unigram_index(self, query_unigrams) -> None:
        for node_id in self.gm.graph.nodes():
            node_data = self.gm.graph.nodes[node_id]
            node_type = node_data.get("type")

            if node_type in self.symbol_generator.grams():
                unigrams = node_id.split("_")
                for unigram in unigrams:
                    if unigram not in query_unigrams:
                        continue
                    if unigram not in self._unigram_index:
                        self._unigram_index[unigram] = set()
                    self._unigram_index[unigram].add(node_id)
    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def extract(self, query: str) -> List[str]:
        query_node_id = f"query::{uuid4().hex}"

        try:
            # TODO: resolve the score pipeline
            # symbols = self._add_query_node(query_node_id, query)
            # symbol_scores = self._score_symbols(symbols)
            # element_scores = self._score_elements(symbol_scores)

            # return self.get_scores(symbol_scores, element_scores)

            self._add_query_node(query_node_id, query)
            results = self._traverse(query_node_id)
            return results

        finally:
            self._cleanup(query_node_id)

    def get_scores(self, symbol_scores: Dict[str, List[str]], element_scores: Dict[str, List[str]]):
        def score_key(item): return (-round(item[1], 6), item[0])

        ranked_symbols = sorted(symbol_scores.items(), key=score_key)
        ranked_elements = sorted(element_scores.items(), key=score_key)

        if self.max_matches is not None and self.max_matches > 0:
            ranked_symbols = ranked_symbols[:self.max_matches]
            ranked_elements = ranked_elements[:self.max_matches]

        matched_symbols = []
        matched_elements = []
        for symbol, score in ranked_symbols:
            matched_symbols.append({"id": symbol,
                                    "content": self.gm.graph.nodes[symbol].get("text"),
                                    "type": self.gm.graph.nodes[symbol].get("type"),
                                    "score": score})
        for element, score in ranked_elements:
            matched_elements.append({"id": element,
                                     "content": self.gm.graph.nodes[element].get("text"),
                                     "type": self.gm.graph.nodes[element].get("type"),
                                     "metadata": self.gm.graph.nodes[element].get("metadata"),
                                     "score": score})

        return {"elements": matched_elements, "symbols": matched_symbols}

    # ─────────────────────────────────────────────────────────────
    # Query Node + Symbol Wiring
    # ─────────────────────────────────────────────────────────────

    def _add_query_node(self, query_node_id: str, query: str) -> None:
        label = (query[:30] + "...") if len(query) > 30 else query

        self.gm.graph.add_node(
            query_node_id,
            type="query@temp",
            label=label,
        )

        tokens = self.tokenizer.tokenize(query)
        symbols = self.symbol_generator.generate(tokens)

        # Only link to symbols that already exist in the graph
        for symbol_list in symbols.values():
            for symbol in symbol_list:
                if symbol in self.gm.graph:
                    self.gm.graph.add_edge(query_node_id, symbol)

        # Build unigram index for partial matching
        self._build_unigram_index(symbols.get("unigram", []))

        return symbols

    # ─────────────────────────────────────────────────────────────
    # Traversal Logic (Trigram → Bigram → Unigram)
    # ─────────────────────────────────────────────────────────────

    def _score_symbols(self, symbols: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Score symbols based on:
        1. Exact matches from the query (highest priority)
        2. Partial matches - symbols containing query unigrams (with containment rule)
        """
        symbol_scores: Dict[str, float] = {}

        # Step 1: Exact matches (original behavior)
        for symbol_type, symbol_list in symbols.items():
            weight = NGRAM_WEIGHTS.get(symbol_type, 1)

            for symbol in symbol_list:
                if symbol not in self.gm.graph:
                    continue
                symbol_scores[symbol] = symbol_scores.get(symbol, 0.0) + weight

        # Extract all query unigrams for partial matching
        query_unigrams = set(symbols.get("unigram", []))

        # Step 2: Partial matches - symbols containing query unigrams
        # Use inverted index for O(matches) lookup instead of O(graph) scan
        for query_unigram in query_unigrams:
            if query_unigram not in self._unigram_index:
                continue

            for node_id in self._unigram_index[query_unigram]:
                # Skip if already matched exactly
                if node_id in symbol_scores:
                    continue

                node_data = self.gm.graph.nodes[node_id]
                node_type = node_data.get("type")

                # Only process symbol nodes (safety check)
                if node_type not in self.symbol_generator.grams():
                    continue

                # Apply containment rule: require at least ceil(len(symbol_unigrams)/2) overlap
                symbol_unigrams = set(node_id.split("_"))
                overlap = symbol_unigrams & query_unigrams
                min_overlap = math.ceil(len(node_id.split("_")) / 2)

                if len(overlap) >= min_overlap:
                    # Score based on node type with partial discount
                    weight = NGRAM_WEIGHTS.get(node_type, 1)
                    symbol_scores[node_id] = symbol_scores.get(
                        node_id, 0.0) + weight * PARTIAL_FACTOR

        return symbol_scores

    def _score_elements(self, symbol_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Propagate symbol scores to connected element nodes via:
        - 'contains' edges (for symbol nodes)
        Since the graph is undirected, edges can be traversed in reverse.

        Applies edge-type weighting, contribution capping, and lexical degree normalization.
        """
        element_scores: Dict[str, float] = {}
        lexical_degrees: Dict[str, int] = {}

        for symbol, score in symbol_scores.items():
            for neighbor in self.gm.graph.neighbors(symbol):
                neighbor_data = self.gm.graph.nodes[neighbor]
                if neighbor_data.get("type") != "element":
                    continue

                edge_data = self.gm.graph.get_edge_data(symbol, neighbor) or {}
                edge_type = edge_data.get("type")

                if edge_type is not None and edge_type != "contains":
                    continue

                # Apply edge-type weighting
                edge_weight = EDGE_WEIGHTS.get(edge_type, 1.0)
                contribution = score * edge_weight

                # Cap contribution to prevent runaway boosting
                contribution = min(contribution, MAX_EDGE_CONTRIBUTION)

                # Compute lexical degree if not cached (only count "contains" edges)
                if neighbor not in lexical_degrees:
                    degree = sum(
                        1 for _, _, d in self.gm.graph.edges(neighbor, data=True)
                        if d.get("type") in ("contains")
                    )
                    lexical_degrees[neighbor] = max(degree, 1)
                # Normalize by lexical degree
                normalized_contribution = contribution / \
                    math.sqrt(lexical_degrees[neighbor])

                element_scores[neighbor] = element_scores.get(
                    neighbor, 0.0) + normalized_contribution

        return element_scores

    def _traverse(self, query_node_id: str) -> List[str]:

        for symbol_type in self.symbol_generator.grams():
            elements, symbols = self._collect_paragraphs(
                query_node_id,
                symbol_type
            )
            if elements:
                # sort by match strength
                return self.get_scores({k[0]: k[1] for k in symbols.most_common()}, {k[0]: k[1] for k in elements.most_common()})

        return self.get_scores({}, {})

    def _collect_paragraphs(
        self,
        query_node_id: str,
        symbol_type: str
    ) -> Counter:

        symbols = Counter()
        elements = Counter()

        for symbol in self.gm.graph.neighbors(query_node_id):
            if self.gm.graph.nodes[symbol].get("type") != symbol_type:
                continue

            for neighbor in self.gm.graph.neighbors(symbol):
                node_type = self.gm.graph.nodes[neighbor].get("type")

                # skip the temporary query node itself
                if node_type not in ["paragraph", "table"]:
                    continue

                elements[neighbor] += 1
                symbols[symbol] += 1

        return elements, symbols

    # ─────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────

    def _cleanup(self, query_node_id: str) -> None:

        if query_node_id not in self.gm.graph:
            return

        connected_symbols = list(self.gm.graph.neighbors(query_node_id))

        self.gm.graph.remove_node(query_node_id)

        # Remove orphan symbols
        for symbol in connected_symbols:
            if symbol not in self.gm.graph:
                continue
            if self.gm.graph.degree(symbol) == 0:
                self.gm.graph.remove_node(symbol)
