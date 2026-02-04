# package_text_tokenizer/tokenizer.py

import re
from typing import List


class TextTokenizer:
    """
    Tokenizes and normalizes text.
    """

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return tokens
