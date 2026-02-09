# package_symbol_generator/symbol_generator.py

from typing import List, Dict


class SymbolGenerator:
    """
    Generates symbolic units from tokens.
    """

    def generate(self, tokens: List[str]) -> Dict[str, List[str]]:
        unigrams = tokens
        bigrams = [
            f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        trigrams = [
            f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}"
            for i in range(len(tokens) - 2)
        ]

        return {
            "unigram": unigrams,
            "bigram": bigrams,
            "trigram": trigrams,
        }

    def grams(self) -> List[str]:
        return ["unigram", "bigram", "trigram"]

    def max_gram(self, tokens: List[str]):
        return "_".join(tokens)
