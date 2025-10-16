## CodeGraph (Python-only)

### What it builds
- Symbols: modules/classes/functions/variables with FQNs, source file, [start,end] lines, docstring, signature, returns.
- Imports graph: absolute, relative, aliasing; star imports expanded; re-exports via `__all__` honored.
- Calls: static edges (name/attr), decorator edges, heuristics for `getattr(mod, "name")` and literal `importlib.import_module("pkg.mod")`.
- Tests: pytest node-ids for top-level `test_*` and `Test*::test_*` (+ basic parametrize expansion).
- Coverage: optional attach from coverage.py XML; per-symbol coverage ratio.
- Incremental rebuild: hash+mtime tracked; reindex changed/added/removed files and reverse-import dependents; then expand stars + re-resolve calls.

### CLI quick reference
```bash
# Summary / rebuild
python -m tools.code_graph ./repo --dump
python -m tools.code_graph ./repo --no-cache --dump

# Query
python -m tools.code_graph ./repo --defs-in package.module
python -m tools.code_graph ./repo --owners-of SymbolName
python -m tools.code_graph ./repo --calls-of package.module.func
python -m tools.code_graph ./repo --who-calls package.module.func
python -m tools.code_graph ./repo --module-deps package.module
python -m tools.code_graph ./repo --pytest-nodes tests.package.test_module
python -m tools.code_graph ./repo --search "class\s+Config"
python -m tools.code_graph ./repo --unresolved   # unresolved (non-builtin) call sites

# Export
python -m tools.code_graph ./repo --export graph.json
python -m tools.code_graph ./repo --export-sqlite graph.db
```

### JSON export (shape)
```json
{
  "root": "...",
  "files": ["pkg/mod.py", ...],
  "symbols": [{
    "fqn": "pkg.mod.Class.method",
    "name": "method",
    "qualname": "Class",
    "kind": "function",
    "module": "pkg.mod",
    "file": "/abs/path/repo/pkg/mod.py",
    "line": 42,
    "end_line": 88,
    "doc": "...",
    "signature": "(x:int,y:int)",
    "returns": "int"
  }],
  "modules": { "pkg.mod": {"file": "...", "is_test": false, "imports": {...}, "defs": ["..."], "exports": ["..."] }},
  "calls": [["caller_fqn", "callee_fqn_or_key"], ...],
  "module_to_tests": {"pkg": ["tests.pkg.test_mod"]},
  "coverage_files": {"pkg/mod.py": [12,13,14]},
  "symbol_coverage": {"pkg.mod.func": 0.75},
  "module_imports": {"pkg.mod": ["pkg.util", "pkg.core"]}
}
```

### SQLite export (tables)
- files(path PK)
- modules(module PK, file, is_test)
- symbols(fqn PK, name, qualname, kind, module, file, line, end_line, doc, signature, returns)
- calls(caller, callee)
- tests_map(module, test_module)
- coverage(file, line)
- mod_deps(module, dep)

Recommended indices: `CREATE INDEX IF NOT EXISTS ix_calls_callee ON calls(callee);` etc.

### How Coding-AI uses CodeGraph
- Planner
  - Parse objective/files; map to symbols and modules via owners/defs.
  - Compute impacted modules: touched + reverse-import dependents.
  - Select tests: `module_to_tests` + `pytest-nodes` for those modules; optionally subset by changed functions (via calls graph).
- Actuator (Patch Generator)
  - Provide file/symbol context (defs, signatures, docstrings, call sites) to the LLM.
  - Use `module_deps` to keep import invariants stable in diffs.
- Verifiers
  - Static/tests/runtime target only impacted modules first; escalate to wider runs if budget remains.
  - Attach coverage; gate on per-symbol coverage regressions (optional).
- Updater (Memory)
  - Store “Lesson Cards” keyed by modules/symbols; leverage owners/callers to retrieve relevant cards as few-shot context.

### Production guidance
- Keep a warm cache: the graph auto-increments on edits; seed with `--no-cache` in CI nightly if needed.
- Use `--unresolved` to monitor dynamic patterns; prefer refactors that reduce unresolved call sites.
- Persist SQLite in CI for artifacted, queryable reports (e.g., changed modules → tests to run).
- For very large repos, shard parse by top-level packages and merge symbol JSON-lines.

### Limitations (by design)
- Dynamic/reflected imports and non-literal getattr are reported rather than “guessed”.
- Decorator semantics are captured as edges but not behaviorally inlined.
- Pytest parametrize expansion is best-effort for literal cases; for full fidelity, run `pytest --collect-only` and cache ids.


