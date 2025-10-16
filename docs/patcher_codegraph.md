### Patcher & CodeGraph

Patcher
- Input: step spec {objective, files, invariants, tests_to_run}
- Output: unified diff
- Strategy: AST codemods for bulk edits; LLM diffs for novel logic
- Conflicts: three-way merge; on reject, shrink hunks and retry

CodeGraph
- Start: ctags symbols + ripgrep references
- Upgrade: tree-sitter index + SQLite FTS5 for queries (owners, call sites)


