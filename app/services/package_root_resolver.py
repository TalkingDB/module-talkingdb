# package_root_resolver/root_resolver.py

from typing import Dict, List


class RootResolver:
    """
    Resolves symbols to canonical root forms.
    """

    def resolve(self, symbols: Dict[str, List[str]]) -> Dict[str, List[str]]:
        resolved: Dict[str, List[str]] = {}

        for level, values in symbols.items():
            resolved[level] = [self._normalize(v) for v in values]

        return resolved

    def _normalize(self, symbol: str) -> str:
        # Placeholder for stemming / synonym logic
        return symbol.rstrip("s")
