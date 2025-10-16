## CodeGraph completion plan (Python-only)

### Scope and goals
- Single-language: Python
- Accurate symbol graph (modules/classes/functions/variables) with FQNs
- High-fidelity call graph for static cases; pragmatic heuristics for dynamic
- Precise imports graph including star imports and re-exports
- Reliable, fast incremental rebuilds
- Verifier-ready exports (JSON + SQLite) for downstream tools

### Work items

- [ ] Re-export chains across packages
  - Follow `__all__` across nested packages and intermediate modules (A.* → B.* → C.symbols)
  - Track aliasing on `from X import Y as Z` in exports and preserve original FQNs in metadata
  - Acceptance: `--refs-of` resolves re-exported symbols to source module FQNs

- [ ] Decorator semantics beyond edges
  - Detect common wrapper patterns (functools.wraps; simple pass-through wrappers) and map wrapper → wrapped
  - Annotate call edges with `kind={direct,decorator,heuristic}`
  - Acceptance: `--calls-of` includes wrapped function edges with `kind=decorator`

- [ ] Dynamic/reflective calls (heuristics)
  - Extend getattr resolution: literals from tuples/dicts, simple f-strings with constants
  - Recognize `importlib.import_module("pkg.mod")` when literal; bind to module symbol space
  - Optional: recognize `__getattr__` in packages to avoid over-resolving
  - Acceptance: literal-based dynamic imports produce stable edges; non-literal remain annotated `kind=unknown`

- [ ] Richer pytest node mapping
  - Expand `@pytest.mark.parametrize` with ids/values (static when literals)
  - Collect class-level and module-level fixtures (names only) and attach to node metadata
  - Optional: `--collect-pytest` integration to shell out `pytest --collect-only -q` and cache nodeids
  - Acceptance: `--pytest-nodes <module>` matches pytest collection output for literal cases

- [ ] Incremental rebuild (fine-grained)
  - Keep reverse import graph persisted; on change, invalidate only impacted modules
  - Hash + mtime already implemented; add file removal detection to purge modules (done: verify with tests)
  - Re-run post passes (star expansion + call re-resolution) only for impacted modules
  - Acceptance: edit one file in a 1k-file repo → rebuild < 400ms on warm cache (target on this machine)

- [ ] Signature/doc improvements
  - Capture defaults, varargs, kw-only args, type comments (`# type: ...`), and PEP 604 `X|Y`
  - Normalize return annotations and strip forward-ref quotes
  - Acceptance: exported `signature` reflects arg kinds and defaults for representative functions

- [ ] CLI/Export polish
  - Add `--dump-module <module>` to show defs/imports/exports/callers/callees
  - Add `--json-lines` stream for symbols/calls to support large repos
  - SQLite: add indices on `symbols(module)`, `calls(callee)`, `mod_deps(dep)`
  - Acceptance: queries over SQLite are sub-50ms on current repo

- [ ] Performance & memory
  - Parallel parse on CPU cores; shard by directory; safe AST-only workers
  - Optional: cache ASTs or symbol summaries per file for faster merges
  - Acceptance: cold build < 3s on this repo; memory < 300MB

- [ ] Tests
  - Unit tests for: imports (relative/star/re-export), decorators, getattr/importlib, pytest nodes, incremental rebuild
  - Golden outputs for small fixture repos; CI job to guard regressions
  - Acceptance: CI green; coverage > 85% for `tools/code_graph.py`

### Nice-to-haves (later)
- Module-level `__getattr__`/`__dir__` semantics awareness
- Cross-file constant propagation for simple dynamic name resolution
- Optional runtime sampling mode to validate static graph against traces

### How to verify
```bash
# Rebuild fresh and export
python -m tools.code_graph ./repo --no-cache --export graph.json --export-sqlite graph.db

# Spot-check module
python -m tools.code_graph ./repo --dump
python -m tools.code_graph ./repo --defs-in <module>
python -m tools.code_graph ./repo --module-deps <module>
python -m tools.code_graph ./repo --calls-of <module.func>
python -m tools.code_graph ./repo --who-calls <module.func>
python -m tools.code_graph ./repo --pytest-nodes <tests.module>
```


