# package_text_tokenizer/tokenizer.py

import spacy
from typing import List
from spacy.matcher import Matcher


class MatchTrainer:
    def __init__(self, nlp: spacy.language.Language):
        self.matcher = Matcher(nlp.vocab)

    def train(self) -> Matcher:
        self.matcher.add(
            "COMPOUND",
            [[
                {"LEMMA": {"IN": [
                    "investigational",
                    "experimental",
                    "study",
                    "test"
                ]}},
                {"POS": "ADJ", "OP": "*"},
                {"LEMMA": {"IN": [
                    "drug",
                    "compound",
                    "substance"
                ]}},
            ]]
        )

        return self.matcher


class TextTokenizer:
    def __init__(self, model: str = "en_core_web_md"):
        self.nlp = spacy.load(
            model,
            disable=["ner", "parser"]
        )

        self.matcher = MatchTrainer(self.nlp).train()

    def tokenize(self, text: str) -> List[str]:
        doc = self.nlp(text.lower())
        matches = self.matcher(doc)

        consumed = set()
        tokens: List[str] = []

        # longest span wins
        matches = sorted(matches, key=lambda m: m[2] - m[1], reverse=True)

        for match_id, start, end in matches:
            if any(i in consumed for i in range(start, end)):
                continue

            for i in range(start, end):
                consumed.add(i)

            label = self.nlp.vocab.strings[match_id]
            tokens.append(label.lower())

        for i, token in enumerate(doc):
            if i in consumed:
                continue
            if token.is_alpha and not token.is_stop:
                tokens.append(token.lemma_)

        return tokens
