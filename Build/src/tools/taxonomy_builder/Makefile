# Makefile — taxonomy_builder
# Run from: Build/src

PY ?= python
PYTEST ?= pytest
PKG ?= tools.taxonomy_builder

# Paths
FIXTURE ?= tools/taxonomy_builder/data/clutch_directory.html
OUT ?= ./data/taxonomy.json
PROFILE ?= dev
TEST_DIR ?= tests/tools/taxonomy_builder

.PHONY: help init selfcheck env run-fixture build-fixture smoke smoke-py test \
	unit parser integration all-tests counts tips clean

help:
	@echo "Targets:"
	@echo "  init           - pip install runtime deps (requirements.txt)"
	@echo "  env            - print where to run and how to set PYTHONPATH" \
	                 "(from Build/src)"
	@echo "  selfcheck      - print entry banner (--self-check)"
	@echo "  run-fixture    - end-to-end build from local HTML fixture"
	@echo "  build-fixture  - alias of run-fixture"
	@echo "  smoke          - run-fixture then show artifact sizes"
	@echo "  smoke-py       - verify outputs exist and are non-empty via Python"
	@echo "  unit           - run unit tests (slugify/urls/backoff)"
	@echo "  parser         - run parser tests on fixtures"
	@echo "  integration    - end-to-end test on fixture"
	@echo "  all-tests      - run full pytest suite"
	@echo "  counts         - print item type counts from data/taxonomy.json"
	@echo "  tips           - common pitfalls and fixes"
	@echo "  clean          - remove generated outputs in ./data"

init:
	$(PY) -m pip install -r $(PKG)/requirements.txt || true

env:
	@echo "Run from: /Users/kevinnovanta/workflow_accelerator/Demos/Prospect_Data_Seeder/Build/src"
	@echo "Activate your venv, then: export PYTHONPATH=."

selfcheck:
	PYTHONPATH=. $(PY) -m $(PKG) --self-check

# Build from the local HTML fixture (offline, deterministic)
run-fixture:
	@mkdir -p ./data
	PYTHONPATH=. $(PY) -m $(PKG) build \
	  --profile $(PROFILE) \
	  --html $(FIXTURE) \
	  --out $(OUT)

build-fixture: run-fixture

# Smoke runs build-fixture and prints sizes of artifacts
smoke: run-fixture
	@echo "--- sizes ---"
	@/bin/ls -lh ./data/taxonomy.json ./data/choices.json || true

# Pythonic smoke validation (existence + non-empty + summary)
smoke-py: run-fixture
	@PYTHONPATH=. $(PY) - <<-'PY'
	from pathlib import Path
	import json

	tax = Path('data/taxonomy.json'); cho = Path('data/choices.json')
	assert tax.exists() and tax.stat().st_size > 0, "taxonomy.json missing/empty"
	print("taxonomy.json:", tax.stat().st_size, "bytes")
	if cho.exists():
	    print("choices.json:", cho.stat().st_size, "bytes")
	doc = json.loads(tax.read_text())
	print("items:", len(doc.get("items", [])))
	print("first:", doc["items"][0] if doc.get("items") else None)
	PY

# Test suites
unit:
	PYTHONPATH=. $(PYTEST) -q $(TEST_DIR)/unit

parser:
	PYTHONPATH=. $(PYTEST) -q $(TEST_DIR)/parser

integration:
	PYTHONPATH=. $(PYTEST) -q $(TEST_DIR)/integration/test_runner_fixture.py

all-tests:
	PYTHONPATH=. $(PYTEST) -q

# Handy: print type coverage after a run
counts:
	@PYTHONPATH=. $(PY) - <<-'PY'
	import json, pathlib
	p = pathlib.Path('data/taxonomy.json')
	assert p.exists() and p.stat().st_size>0, 'Run `make run-fixture` first'
	doc = json.loads(p.read_text())
	from collections import Counter
	print(Counter(x['type'] for x in doc.get('items', [])))
	PY

# Tips target prints the common pitfalls and fixes from the playbook
tips:
	@echo "Common pitfalls:"; \
	echo "  - No module named tools/taxonomy_builder: run from Build/src and set PYTHONPATH=."; \
	echo "  - Makefile not found: run make from the directory containing this Makefile or use -f."; \
	echo "  - Schema not found: ensure Build/src/schema/taxonomy.schema.json exists (banner shows SCHEMA_EXISTS)."; \
	echo "  - DeprecationWarning (utcnow): informational; not a failure."

clean:
	@rm -f ./data/taxonomy.json ./data/choices.json ./data/deadletter.jsonl
