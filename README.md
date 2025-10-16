## coding-ai (minimal PAVU loop)

### Why this works (PAVU)
- Plan → Act → Verify → Update loop: every change is planned, applied as diffs, verified, and captured as lessons.
- Diffs as currency: repo-wide edits, revertible, auditable.
- Multi-verifier gating: static (ruff/black/mypy) → tests (pytest) → runtime probes.
- Single orchestrator: one `runner.py` drives Planner/Actuator/Verifier/Updater.

### Quick start
1) Place a target repo under `coding-ai/repo` or set `CODE_REPO=...` and symlink.
2) Run:
```bash
python runner.py --task "Refactor logging; add retry to client"
```
3) Output shows pass/fail and an example diff (stubbed initially).

### Model setup (Hugging Face Llama-3 8B Instruct)
- Accept the license and request access on the model page: [meta-llama/Meta-Llama-3-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- Set your token in env:
```bash
export HF_TOKEN=hf_...   # or HUGGINGFACEHUB_API_TOKEN
```
- Optional overrides:
```bash
export HF_MODEL_ID=meta-llama/Meta-Llama-3-8B-Instruct
```

### Directory layout
- `runner.py`: Orchestrator.
- `planning/`: `planner.py` builds step specs (objective, files, tests, risks).
- `act/`: `patcher.py` proposes and applies unified diffs (dry-run first).
- `verify/`: `static.py`, `tests.py`, `runtime.py` run gates.
- `update/`: `updater.py` records lessons, updates graph.
- `tools/`: `code_graph.py` repo symbol graph (ctags/tree-sitter later).
### CodeGraph docs
See `docs/code_graph.md` for architecture, CLI, exports, incremental rebuilds, and how the Planner/Actuator/Verifier/Updater use it in production.
- `configs/`: `policy.yaml` gates/timeouts, `sandbox.yaml` limits/network.
- `logs/`: artifacts (to be populated by runner).
 - `llm_client.py`: HF client for Meta-Llama-3-8B-Instruct.

### Wiring the verifiers (minimal)
Implemented minimal verifiers:
- `verify/static.py`: runs `ruff`, `black --check`, `mypy --strict` if available.
- `verify/tests.py`: runs `pytest -q --maxfail=1`, accepts `-k` patterns.
- `verify/runtime.py`: placeholder (add your smoke checks).

Run all verifiers:
```bash
make verify
```

### CodeGraph usage
Build/inspect graph:
```bash
make graph                         # summary
python -m tools.code_graph ./repo --owners-of Client  # owners of symbol
python -m tools.code_graph ./repo --search "def request\("  # ripgrep
```
Current stubs always pass. Replace bodies:
- `verify/static.py`: run `ruff`, `black --check`, `mypy --strict`.
- `verify/tests.py`: run `pytest -q --maxfail=1` optionally filtering by touched files.
- `verify/runtime.py`: run a smoke CLI or HTTP mock.

### Sandbox
`configs/sandbox.yaml` defines an offline container profile (python:3.11-slim). Integrate your Docker/Podman runner to execute verifiers inside the sandbox before merging patches.

### Patcher
`act/patcher.py` should emit unified diffs (git-style), dry-run apply in a temp copy of the repo, then hand off to verifiers. On reject/conflict, narrow the patch and re-propose.

### CodeGraph
`tools/code_graph.py` is a placeholder. Start with ctags for symbols and ripgrep for references; upgrade to tree-sitter + SQLite FTS5 for richer indexing.

### Roadmap
- Replace stubs with real commands.
- Add HTML reports and artifact bundling under `logs/`.
- Record “Lesson Cards” per successful run to reuse as few-shot prompts.
- Advanced features docs:
  - RLHF on verifier rewards: docs/advanced/rlhf.md
  - Memory / Lesson Cards: docs/advanced/memory.md
  - Spec synthesizer: docs/advanced/spec_synth.md
  - Semantic search: docs/advanced/semantic_search.md


