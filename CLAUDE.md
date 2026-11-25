# CLAUDE.md — demo-app

Small Python demo app used to exercise the ai-sdlc pipeline end to end.

## Stack
- Python 3.12, standard library only (no new runtime dependencies without a design note)
- Tests: pytest

## Layout
- `src/demo_app/` — application package (src layout)
- `tests/` — pytest tests, one `test_<module>.py` per module
- `docs/designs/` — technical designs written by the Architect agent (do not edit by hand in a story)

## Commands
- Install: `pip install -e '.[dev]'`
- Test: `pytest -q`

## Conventions
- Type hints on all public functions; short docstrings
- Pure functions where possible; raise `ValueError` for invalid input
- If adding a CLI, use `argparse` in `src/demo_app/cli.py` with a `main(argv: list[str] | None = None) -> int` entry point
- Keep each change small and covered by tests
