# Testing the Black Circuit — DM TUI

## Quickstart
```bash
python -m pip install -r requirements-dev.txt
pytest
```

If you haven't installed the package in editable mode yet, imports still work
because `tests/conftest.py` adds the repo root to `sys.path` during tests.

## What gets tested today
- `parse()` accepts standard and weird dice (d5, d7, d14, d16, d24, d30).
- `roll()` totals are deterministic via monkeypatched `random.randint`.
- Exploding dice and keep-high/keep-low semantics are validated.