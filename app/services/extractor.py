from typing import Dict, List
from collections import Counter

from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.helpers.graph_cache import graph_cache
from app.core.thread_pool import executor


class ExtractorService:

    def __init__(self, graph_ids: List[str], max_matches: int = 10):
        self.gms = [graph_cache.get(gid) for gid in graph_ids]

        self.max_matches = max_matches
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()

        self.executor = executor

    # ─────────────────────────────────────────────────────────────

    def extract(self, query: str):

        tokens = self.tokenizer.tokenize(query)
        symbols = self.symbol_generator.generate(tokens)

        for symbol_type in self.symbol_generator.grams():

            elements, matched_symbols = self._collect_paragraphs(
                symbols.get(symbol_type, []),
                symbol_type
            )

            if elements:
                return self.get_scores(matched_symbols, elements)

        return self.get_scores({}, {})

    # ─────────────────────────────────────────────────────────────

    def _collect_paragraphs(
        self,
        query_symbols: List[str],
        symbol_type: str,
    ):

        def process_graph(gm):
            local_symbols = Counter()
            local_elements = Counter()

            graph = gm.graph

            for symbol in query_symbols:

                if symbol not in graph:
                    continue

                if graph.nodes[symbol].get("type") != symbol_type:
                    continue

                for neighbor in graph.neighbors(symbol):
                    node_type = graph.nodes[neighbor].get("type")

                    if node_type not in ("paragraph", "table"):
                        continue

                    element_id = f"{gm.graph_id}##{neighbor}"
                    symbol_id = f"{gm.graph_id}##{symbol}"

                    local_elements[element_id] += 1
                    local_symbols[symbol_id] += 1

            return local_elements, local_symbols

        elements_counter = Counter()
        symbols_counter = Counter()

        futures = [
            self.executor.submit(process_graph, gm)
            for gm in self.gms
        ]

        for future in futures:
            el_counter, sym_counter = future.result()
            elements_counter.update(el_counter)
            symbols_counter.update(sym_counter)

        return elements_counter, symbols_counter
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

        for full_id, score in ranked_symbols:
            graph_id, symbol = full_id.split("##", 1)
            graph = graph_cache.get(graph_id).graph

            matched_symbols.append({
                "id": symbol,
                "graph_id": graph_id,
                "content": graph.nodes[symbol].get("text"),
                "type": graph.nodes[symbol].get("type"),
                "score": score,
            })

        for full_id, score in ranked_elements:
            graph_id, element = full_id.split("##", 1)
            graph = graph_cache.get(graph_id).graph

            matched_elements.append({
                "id": element,
                "graph_id": graph_id,
                "content": graph.nodes[element].get("text"),
                "type": graph.nodes[element].get("type"),
                "metadata": graph.nodes[element].get("metadata"),
                "score": score,
            })

        return {
            "elements": matched_elements,
            "symbols": matched_symbols,
        }
