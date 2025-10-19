.PHONY: demo fmt tree

demo:
	python -m baator_sim.demo

fmt:
	python -m pip install ruff black || true
	ruff check --fix src || true
	black src || true

tree:
	python - <<'PY'
import os
for r, d, f in os.walk('.', topdown=True):
    d[:] = [x for x in d if x not in {'.git', '__pycache__'}]
    level = r.count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(r)}/")
    for name in f:
        print(f"{indent}  {name}")
PY