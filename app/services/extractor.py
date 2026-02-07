# app/services/extractor.py

import networkx as nx
from typing import List, Set
from uuid import uuid4

from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.models.graph.graph import GraphModel
from collections import Counter


class ExtractorService:

    def __init__(self, graph_id: str, depth: int = 2):
        with sqlite_conn() as conn:
            self.gm = GraphModel.load(conn, graph_id)

        self.depth = depth
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def extract(self, query: str) -> List[str]:
        query_node_id = f"query::{uuid4().hex}"

        try:
            self._add_query_node(query_node_id, query)
            results = self._traverse(query_node_id)
            return list(results)

        finally:
            self._cleanup(query_node_id)

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
        for symbol_type, symbol_list in symbols.items():
            for symbol in symbol_list:
                if symbol in self.gm.graph:
                    self.gm.graph.add_edge(query_node_id, symbol)

    # ─────────────────────────────────────────────────────────────
    # Traversal Logic (Trigram → Bigram → Unigram)
    # ─────────────────────────────────────────────────────────────

    def _traverse(self, query_node_id: str) -> List[str]:

        for symbol_type in ("trigram", "bigram", "unigram"):
            counter = self._collect_paragraphs(
                query_node_id,
                symbol_type
            )
            if counter:
                # sort by match strength
                return counter.most_common()

        return []


    def _collect_paragraphs(
        self,
        query_node_id: str,
        symbol_type: str
    ) -> Counter:

        results = Counter()

        for symbol in self.gm.graph.neighbors(query_node_id):
            if self.gm.graph.nodes[symbol].get("type") != symbol_type:
                continue

            for neighbor in self.gm.graph.neighbors(symbol):
                node_type = self.gm.graph.nodes[neighbor].get("type")

                # skip the temporary query node itself
                if node_type == "query@temp":
                    continue

                label = self.gm.graph.nodes[neighbor].get("label")
                if label:
                    results[label] += 1

        return results


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
