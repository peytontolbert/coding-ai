### Verifiers

Static checks (examples):
```bash
ruff check .
black --check .
mypy --strict .
```

Tests:
```bash
pytest -q --maxfail=1
```

Runtime probes:
```bash
python scripts/smoke.py
```

Integrate these into `verify/static.py`, `verify/tests.py`, `verify/runtime.py` using `subprocess.run` and return booleans.


