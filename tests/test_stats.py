from pathlib import Path

import pytest

from demo_app.stats import TextStats, compute_stats, tokenize


def test_basic():
    assert compute_stats("the cat the dog") == TextStats(
        4, 3, [("the", 2), ("cat", 1), ("dog", 1)]
    )


def test_case_insensitive():
    s = compute_stats("The the THE")
    assert (s.word_count, s.unique_word_count) == (3, 1)


def test_punctuation_ignored():
    s = compute_stats("hello, hello! (hello)")
    assert s.top_words == [("hello", 3)]


def test_apostrophes():
    assert tokenize("don't") == ["don't"]
    assert tokenize("don’t") == ["don't"]
    assert tokenize("'hi'") == ["hi"]


def test_tie_break_alphabetical():
    assert compute_stats("b a c", 3).top_words == [("a", 1), ("b", 1), ("c", 1)]


@pytest.mark.parametrize("text", ["", "   \n\t", "...,!?"])
def test_empty_like(text):
    assert compute_stats(text) == TextStats(0, 0, [])


def test_top_n_bounds():
    assert len(compute_stats("a b", 10).top_words) == 2
    assert compute_stats("a b", 0).top_words == []


def test_negative_top_n():
    with pytest.raises(ValueError):
        compute_stats("a", -1)


def test_quack_comments():
    root = Path(__file__).resolve().parent.parent
    for path in (root / "src/demo_app/stats.py", Path(__file__)):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") and not line.startswith("#!"):
                assert line.startswith("# QUACK!"), (path, line)
