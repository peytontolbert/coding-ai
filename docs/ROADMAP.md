## Structured next steps (feature branches, test-before-merge)

Branch naming: `feature/<area>-<short-goal>`; open PR; require green CI (`scripts/ci_verify.sh`) before merge.

### 1) Actuator (diff generation + safe apply)
- [ ] Prompt LLM with CodeGraph context (defs, callers, owners) to generate unified diffs
- [ ] Apply diffs in a temp copy; prefer three-way merge; on reject, auto-split hunks and retry
- [ ] Artifacts: store failed hunks and stats under `logs/`
- [ ] Tests: unit for hunk-splitting; e2e on a small fixture repo

### 2) Runner integration
- [ ] Pass plan’s `tests_to_run` to pytest (done)
- [ ] Save junit XML and coverage; gate if failing or below thresholds
- [ ] Budget/policy: max refine loops, timeouts (from `configs/policy.yaml`)
- [ ] Tests: simulate a failing step and ensure early exit

### 3) Sandbox hardening
- [ ] Implement Docker runner per `configs/sandbox.yaml` (network off, CPU/RAM caps)
- [ ] Bind-mount temp repo copy; run verifiers inside
- [ ] Local fallback when Docker unavailable (done minimal)
- [ ] Tests: mock docker calls; verify commands and env

### 4) Verifiers polish
- [ ] Static: add mypy cache, ruff config; report formatting
- [ ] Tests: seed lint errors in fixture and assert failure paths

### 5) Planner improvements
- [ ] Use CodeGraph to compute impacted modules via reverse imports from changed files
- [ ] Select minimal tests via pytest nodes; escalate scope on flakiness
- [ ] Tests: change one module; ensure correct tests selected

### 6) Memory (Lesson Cards)
- [ ] Persist successful diffs + context keyed by module/symbols
- [ ] Retrieve top‑K for similar tasks (objective + modules overlap)
- [ ] Tests: retrieval ranking on synthetic tasks

### 7) CI/CD
- [ ] Add GitHub Actions workflow to run `scripts/ci_verify.sh`
- [ ] Cache pip, mypy, ruff; upload artifacts on failure (junit, logs)
- [ ] Branch protection: require green status

### 8) Documentation
- [ ] CONTRIBUTING.md: branching, PR checks, CI
- [ ] Update README with developer workflow
- [ ] User guide for configuring sandbox and policies

### 9) Performance targets
- [ ] Cold CodeGraph build < 3s on this repo
- [ ] Incremental < 400ms for single-file edits
- [ ] Parallel parse across cores

### 10) Observability
- [ ] Structured logs (JSON) for each step; timestamps and durations
- [ ] Optional HTML report per run under `logs/`


