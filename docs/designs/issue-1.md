# Technical Design: Text statistics (Issue #1)

## 1. Architectural Approach
The feature adds two modules to the existing `src/demo_app/` package (src layout, stdlib only, Python 3.12). `stats.py` holds a pure function that tokenizes text with a single compiled `re` pattern and counts with `collections.Counter`. `cli.py` is a thin `argparse` layer that reads a UTF-8 file, calls the stats function, and formats output. No new dependencies or `pyproject.toml` changes are needed.

## 2. Data Models, Interfaces & Signatures
```python
# src/demo_app/stats.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TextStats:
    word_count: int                      # total tokens
    unique_word_count: int               # distinct tokens (case-insensitive)
    top_words: list[tuple[str, int]]     # (word, count), count desc, then word asc

def tokenize(text: str) -> list[str]:
    """Lowercase text and return words. Word = [^\W_]+ with inner apostrophes
    allowed: regex r"[^\W_]+(?:'[^\W_]+)*" applied to text.lower().
    Curly apostrophe (U+2019) is normalized to "'" first."""

def compute_stats(text: str, top_n: int = 10) -> TextStats:
    """Raise ValueError if top_n < 0."""

# src/demo_app/cli.py
def build_parser() -> argparse.ArgumentParser: ...
def main(argv: list[str] | None = None) -> int: ...
# if __name__ == "__main__": raise SystemExit(main())
```

CLI output format (stable):
```
Words: 12
Unique words: 8
Top 3 words:
  the  4
  cat  2
  sat  1
```
(word left-aligned padded to the longest word shown, two spaces, count.) If there are no words, the "Top" section prints `Top 0 words:` with no lines (header uses the actual number of rows shown).

## 3. Verification Approach
- **Test Command:** `pytest -q`
- One test file per module: `tests/test_stats.py`, `tests/test_cli.py`.
- CLI tests call `main([...])` directly with files from `tmp_path` and use `capsys` for stdout/stderr; no subprocess needed except one optional `python -m demo_app.cli` smoke test via `subprocess.run([sys.executable, "-m", "demo_app.cli", ...])`.
- Invalid-argument cases: argparse exits via `SystemExit(2)`; `main` catches it and returns the code so callers always get an `int`.

## 4. Story Implementation Plan

### Story 1: Text statistics function
- **New files:**
  - `src/demo_app/stats.py` — `TextStats`, `tokenize`, `compute_stats`.
  - `tests/test_stats.py` — unit tests.
- **Modified files:** none.
- **Steps:**
  1. Define a module-level compiled `_WORD_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*")`.
  2. Implement `tokenize`: replace `’` with `'`, `.lower()`, `_WORD_RE.findall`.
  3. Implement `compute_stats`: raise `ValueError("top_n must be >= 0")` if `top_n < 0`; tokenize; `Counter`; `top_words = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]`; return `TextStats(len(tokens), len(counter), top_words)`.
  4. Add type hints and short docstrings.
- **Tests:**
  - Basic: `"the cat the dog"` → word_count 4, unique 3, top `[("the", 2), ("cat", 1), ("dog", 1)]`.
  - Case-insensitive: `"The the THE"` → unique 1, count 3.
  - Punctuation ignored: `"hello, hello! (hello)"` → one word, count 3.
  - Apostrophe kept: `"don't"` → `["don't"]`; leading/trailing quotes `"'hi'"` → `["hi"]`.
  - Tie-break alphabetical: `"b a c"` with top 3 → a, b, c.
  - Empty, whitespace-only, punctuation-only → `TextStats(0, 0, [])`.
  - `top_n` greater than unique returns all; `top_n=0` returns `[]`.
  - Negative `top_n` raises `ValueError`.

### Story 2: `stats` CLI command
- **New files:**
  - `src/demo_app/cli.py` — parser, `stats` subcommand, `main`, `__main__` guard.
  - `tests/test_cli.py` — CLI tests.
- **Modified files:** none (depends on `demo_app.stats` from Story 1).
- **Steps:**
  1. `build_parser()`: `ArgumentParser(prog="demo_app.cli")`, subparsers with `dest="command"`, `required=True`; `stats` subparser with positional `file` (`type=pathlib.Path`) and `--top` (`type=_non_negative_int`, default 10). `_non_negative_int` raises `argparse.ArgumentTypeError` for non-integers and negatives so argparse reports the error (exit 2).
  2. `main(argv)`: wrap `parser.parse_args(argv)` in `try/except SystemExit as e` and return `e.code` as int (0 for `--help`, 2 for errors).
  3. For `stats`: `text = path.read_text(encoding="utf-8")`; catch `OSError` (missing, directory, permission) → print `error: cannot read <file>: <strerror>` to stderr, return 1; catch `UnicodeDecodeError` → print `error: <file> is not valid UTF-8 text` to stderr, return 1.
  4. Call `compute_stats(text, args.top)`, print in the format from section 2, return 0.
  5. Add `if __name__ == "__main__": raise SystemExit(main())`.
- **Tests:**
  - Success: file `"the cat the dog"` → exit 0; stdout contains `Words: 4`, `Unique words: 3`, and `the  2` line.
  - `--top 1` limits to one row; default shows up to 10 rows (file with 12 distinct words → 10 rows).
  - Missing file → returns 1, stderr contains `error:`, stdout empty.
  - Non-UTF-8 file (`write_bytes(b"\xff\xfe\x00")` style invalid bytes such as `b"\xff\xff"`) → returns 1, stderr contains "UTF-8".
  - Directory path → returns 1 (no traceback).
  - `--top -1` and `--top abc` → returns non-zero (2).
  - Missing subcommand → non-zero.
  - Optional subprocess smoke test of `python -m demo_app.cli stats <file>` returns 0.

## 5. Risks & Trade-offs
- **Tokenization:** `[^\W_]` counts Unicode letters/digits, so non-English words work but no language-specific segmentation (CJK is one token per run). Hyphenated words split ("well-known" → "well", "known"); apostrophes inside words are kept (answers the open questions; default `--top` is 10).
- **Memory:** The file is read fully into memory; acceptable for the demo scope.
- **Encoding:** A UTF-8 BOM would appear as a character not matched by the word regex, so it is harmlessly ignored.
- **Exit codes:** 0 success, 1 runtime/file error, 2 usage error (argparse convention).
