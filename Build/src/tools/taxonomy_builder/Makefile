# Makefile — taxonomy_builder
# Run from: Build/src

PY ?= python
PYTEST ?= pytest
HTML_FIXTURE ?= tools/taxonomy_builder/data/clutch_directory.html
OUT ?= ./data/taxonomy.json
PROFILE ?= dev
PKG ?= tools/taxonomy_builder
TEST_DIR ?= tests/tools/taxonomy_builder

.PHONY: help init selfcheck smoke build-fixture test run clean

help:
	@echo "Targets:"
	@echo "  init           - install runtime dependencies (requirements.txt)"
	@echo "  selfcheck      - print entry banner (--self-check)"
	@echo "  build-fixture  - parse fixture HTML -> write data/taxonomy.json & data/choices.json"
	@echo "  smoke          - alias of build-fixture + size summary"
	@echo "  test           - run unit/parser/integration tests (PYTHONPATH=.)"
	@echo "  run            - alias of smoke"
	@echo "  clean          - remove generated outputs in ./data"

init:
	$(PY) -m pip install -r $(PKG)/requirements.txt || true

selfcheck:
	$(PY) -m $(PKG) --self-check

# Build from the local HTML fixture (offline, deterministic)
build-fixture:
	@mkdir -p ./data
	$(PY) -m $(PKG) build \
	  --html $(HTML_FIXTURE) \
	  --out $(OUT) \
	  --profile $(PROFILE)

# Smoke runs build-fixture and prints sizes of artifacts
smoke: build-fixture
	@echo "--- sizes ---"
	@/bin/ls -lh ./data/taxonomy.json ./data/choices.json || true

# Run tests with local package import resolution
test:
	PYTHONPATH=. $(PYTEST) -q $(TEST_DIR)

run: smoke

clean:
	@rm -f ./data/taxonomy.json ./data/choices.json ./data/deadletter.jsonl
