### Policy-gradient fine-tune on verifier rewards (lightweight RLHF)

Idea:
- Treat verifier pass ratio and latency penalties as a scalar reward.
- Use PPO/DPO-like updates on a code-diff model conditioned on plan/context.

MVP loop:
1) Sample diffs from the current policy (LLM) for a batch of objectives.
2) Run verifiers; compute reward per sample.
3) Compute advantages and update policy with clipped PPO or reward-weighted regression.

Notes:
- Keep batch small; cache artifacts.
- Start with offline RLAIF using stored (diff, reward) pairs.


