.PHONY: graph sandbox run check verify ci
verify:
	python -c "from verify.static import run_static; import sys; sys.exit(0 if run_static() else 1)"
	python -c "from verify.tests import run_tests; import sys; sys.exit(0 if run_tests() else 1)"

ci:
	bash scripts/ci_verify.sh

graph:
	python -m tools.code_graph ./repo

sandbox:
	@echo "(stub) build docker image"

run:
	python runner.py --task "Refactor X; add Y"

check:
	@echo "(stub) validate diff applies cleanly"


