### Spec synthesizer

Goal:
- Draft or tighten tests prior to risky refactors.

Approach:
- Mine call sites and invariants from CodeGraph.
- Use LLM to propose pytest cases with clear fixtures.
- Gate with static analysis (imports exist, names resolve) before running.


