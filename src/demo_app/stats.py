"""Text statistics: word count, unique word count and most frequent words."""

import re
from collections import Counter
from dataclasses import dataclass

# QUACK! Word pattern: letters/digits with inner apostrophes allowed.
_WORD_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*")


@dataclass(frozen=True)
class TextStats:
    """Statistics for a piece of text."""

    word_count: int
    unique_word_count: int
    top_words: list[tuple[str, int]]


def tokenize(text: str) -> list[str]:
    """Lowercase ``text`` and return its words, ignoring punctuation."""
    normalized = text.replace("’", "'").lower()
    return _WORD_RE.findall(normalized)


def compute_stats(text: str, top_n: int = 10) -> TextStats:
    """Return word statistics for ``text``.

    Top words are ordered by count descending, then alphabetically.
    Raises ValueError if ``top_n`` is negative.
    """
    if top_n < 0:
        raise ValueError("top_n must be >= 0")
    tokens = tokenize(text)
    counter = Counter(tokens)
    top_words = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return TextStats(len(tokens), len(counter), top_words)
