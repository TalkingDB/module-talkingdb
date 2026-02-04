# package_semantic_extractor/extractor.py

from typing import List
import networkx as nx


class SemanticExtractor:
    """
    Extracts semantically related nodes from the graph.
    """

    def extract(
        self,
        graph: nx.Graph,
        query_symbols: List[str],
        depth: int = 2,
    ) -> List[str]:
        results = set()

        for symbol in query_symbols:
            if symbol not in graph:
                continue

            for node, dist in nx.single_source_shortest_path_length(
                graph, symbol, cutoff=depth
            ).items():
                results.add(node)

        return list(results)
