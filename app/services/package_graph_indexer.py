# package_graph_indexer/graph_indexer.py

import networkx as nx
from typing import Dict, List


class GraphIndexer:
    """
    Builds a semantic graph from symbolic units.
    """

    def __init__(self):
        self.graph = nx.Graph()

    def index(
        self,
        element_id: str,
        symbols: Dict[str, List[str]],
    ) -> nx.Graph:
        for level, values in symbols.items():
            for symbol in values:
                self.graph.add_node(symbol, type=level)
                self.graph.add_edge(element_id, symbol)

        return self.graph
