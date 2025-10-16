.PHONY: graph sandbox run check
verify:
	python - <<'PY'
from verify.static import run_static
from verify.tests import run_tests
ok = run_static()
ok = run_tests() and ok
print('OK' if ok else 'FAIL')
PY

graph:
	python -m tools.code_graph ./repo

sandbox:
	@echo "(stub) build docker image"

run:
	python runner.py --task "Refactor X; add Y"

check:
	@echo "(stub) validate diff applies cleanly"


