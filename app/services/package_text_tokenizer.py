import threading
import spacy
from typing import List
from spacy.matcher import Matcher


class TextTokenizer:
    def __init__(self, model: str = "en_core_web_md"):
        self.model = model
        self._local = threading.local()

    def _get_nlp(self):
        if not hasattr(self._local, "nlp"):
            nlp = spacy.load(
                self.model,
                disable=["ner", "parser"]
            )
            matcher = Matcher(nlp.vocab)

            matcher.add(
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

            matcher.add(
                "SPONSOR",
                [[
                    {"LEMMA": {"IN": ["sponsor", "company"]}}
                ]]
            )

            self._local.nlp = nlp
            self._local.matcher = matcher

        return self._local.nlp, self._local.matcher

    def tokenize(self, text: str, strict: bool = True) -> List[str]:
        nlp, matcher = self._get_nlp()

        doc = nlp(text.lower())
        matches = matcher(doc)

        consumed = set()
        tokens: List[str] = []

        matches = sorted(matches, key=lambda m: m[2] - m[1], reverse=True)

        for match_id, start, end in matches:
            if any(i in consumed for i in range(start, end)):
                continue

            for i in range(start, end):
                consumed.add(i)

            label = nlp.vocab.strings[match_id]
            tokens.append(label.lower())

        for i, token in enumerate(doc):
            if i in consumed:
                continue
            if (not strict or token.is_alpha) and not token.is_stop:
                tokens.append(token.lemma_)

        return tokens
