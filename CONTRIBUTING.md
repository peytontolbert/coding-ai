## Contributing

### Branching
- Use feature branches from `main` or `develop`.
- Suggested prefix: `feature/` (CI also runs on `feature/actuator-safe-apply`).

### PR checks (CI)
- GitHub Actions runs `scripts/ci_verify.sh`:
  - Build CodeGraph (no-cache)
  - Static checks: ruff/black/mypy if available
  - Tests: `pytest -q --maxfail=1` writing `logs/junit.xml` and `logs/coverage.xml`
- On failure, logs are uploaded as artifacts.

### Developer workflow
1. Place or link your target repo under `coding-ai/repo` (or set `CODE_REPO`).
2. Implement changes on a feature branch.
3. Run locally:
   - `make graph`
   - `make verify` (artifacts under `logs/`)
   - `python runner.py --task "Improve X; add Y"`
4. Open a PR; ensure CI is green.


