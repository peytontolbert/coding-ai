### Overview

This project implements a pragmatic Plan → Act → Verify → Update (PAVU) loop for repo-wide code changes with verifiers and sandboxing.

Key pillars:
- Diffs as the only write primitive
- Multi-verifier gating (static/tests/runtime)
- Single orchestrator, resumable runs
- Lightweight CodeGraph for targeted context


