# package_content_elementizer/elementizer.py

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ContentElement:
    id: str
    text: str
    metadata: Dict[str, Any]


class ContentElementizer:
    """
    Converts raw document content into flat content elements.
    """

    def elementize(self, content: str) -> List[ContentElement]:
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

        elements: List[ContentElement] = []
        for idx, para in enumerate(paragraphs):
            elements.append(
                ContentElement(
                    id=f"para_{idx}",
                    text=para,
                    metadata={"index": idx},
                )
            )

        return elements
