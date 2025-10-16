### Memory-augmented few-shot from Lesson Cards

Lesson Card schema:
- objective, repo, diff_signature, failing_signals, verifiers_passed, key_patterns

Usage:
- On new tasks, retrieve top-k similar cards (by objective embedding + file overlap),
  and include snippets in the LLM context to steer diff quality.


