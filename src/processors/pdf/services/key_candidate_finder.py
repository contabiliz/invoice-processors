from ..enums import ExtractionMethod
from ..schemas import FieldSpec, KeyCandidate, WordBox
from ..spatial import find_phrase_line, find_phrase_ngram


class KeyCandidateFinder:
    def find(self, field: FieldSpec, words: list[WordBox]) -> list[KeyCandidate]:
        candidates = []

        for bbox in find_phrase_ngram(field.labels, words):
            candidates.append(
                KeyCandidate(
                    key=field.key,
                    confidence=1.0,
                    method=ExtractionMethod.NGRAM,
                    bbox=bbox,
                )
            )

        for bbox in find_phrase_ngram(field.aliases, words):
            candidates.append(
                KeyCandidate(
                    key=field.key,
                    confidence=0.93,
                    method=ExtractionMethod.ALIAS,
                    bbox=bbox,
                )
            )

        if not candidates:
            for bbox in find_phrase_line(field.labels + field.aliases, words):
                candidates.append(
                    KeyCandidate(
                        key=field.key,
                        confidence=0.85,
                        method=ExtractionMethod.LINE_FALLBACK,
                        bbox=bbox,
                    )
                )

        return candidates
