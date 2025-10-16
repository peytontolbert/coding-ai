### Sandbox

Baseline profile (configs/sandbox.yaml):
- image: python:3.11-slim
- network: off by default
- limits: 2 CPUs, 4GB RAM, PID cap

Implement `sandbox/docker_runner.py` to:
- Build or pull the image
- Mount a repo copy at /workspace
- Run verifiers inside with the configured env/timeouts


