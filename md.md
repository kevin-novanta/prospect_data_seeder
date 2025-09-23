# **Taxonomy Builder — Phase‑Ranked Blueprint (v1)**

  

> Goal: implement **all files** in a reliable order, with a **smoke test at the end of every phase**. Run everything from Build/src unless noted. Output target: Build/src/data/taxonomy.json.

---

## **Phase 0 — Bootstrap & Scaffolding**

  
**Why:** establish package layout, deps, and an output folder so later phases don’t churn.


**Files to touch**

- tools/taxonomy_builder/__init__.py: empty sentinel.
    
- tools/taxonomy_builder/requirements.txt:
    
    - beautifulsoup4==4.12.3
        
    - jsonschema==4.21.1
        
    - requests==2.32.3
        
    - (optional) playwright later
        
    
- tools/taxonomy_builder/logging_setup.py: JSON logger config (basic, INFO default).
    
- tools/taxonomy_builder/config.py: central config (env vars for profile, paths; output dir = ./data).
    
- tools/taxonomy_builder/data/: add fixture clutch_directory.html (copy from screenshot page source later) & taxonomy.sample.json (empty {} placeholder now).
    
- Create ./data/ (top‑level under Build/src/) — holds **outputs**.
    

  

**Smoke test**

- pip install -r tools/taxonomy_builder/requirements.txt
    
- python -c "import tools.taxonomy_builder as x; print('ok')"
    
- Expect: prints ok.
    

---

## **Phase 1 — Entrypoints & CLI**

  
**Why:** a stable invocation surface before internal plumbing.


**Files to implement**

- tools/taxonomy_builder/__main__.py:
    
    - Parse --self-check (delegates to entrypoint banner).
        
    - Else delegate to CLI main().
        
    
- tools/taxonomy_builder/cli.py:
    
    - Subcommand build with flags:
        
        - --html file (fixture path)
            
        - --out file (default ./data/taxonomy.json)
            
        - --profile dev|ci|prod (default dev)
            
        
    - Call runtime_delivery.runner.run_build(...).
        
    
- tools/taxonomy_builder/runtime_delivery/entrypoint.py:
    
    - print_config_banner() summarizing versions and resolved config.
        
    
- tools/taxonomy_builder/runtime_delivery/profiles.py:
    
    - Map dev|ci|prod → knobs (e.g., robots off/on, rate limits).
        
    

  

**Smoke test**

- python -m tools.taxonomy_builder --self-check → banner printed, exit 0.
    
- python -m tools.taxonomy_builder build --help → shows flags.
    

---

## **Phase 2 — Platform & Ops (minimal)**

  

**Why:** guardrails early: governance, security, health, metrics shells.

  

**Files to implement**

- platform_ops/governance.py:
    
    - robots_policy(profile)->bool (dev=false, prod=true now).
        
    - allow_domain(url)->bool (always true for fixture).
        
    
- platform_ops/security.py:
    
    - redact(value:str)->str (mask emails/tokens for logs).
        
    
- platform_ops/observability.py:
    
    - Counters dict (inc(name, **labels)), timers (time_block(name) context manager), flush_metrics() → prints JSON.
        
    
- platform_ops/health.py:
    
    - readiness()->dict (return static OK), liveness()->dict (OK).
        
    

  

**Smoke test**

- python - <<'PY' from tools.taxonomy_builder.platform_ops import governance, security, observability, health print(governance.robots_policy('dev')) print(security.redact('token_abc123')) with observability.time_block('demo'): pass observability.inc('runs_started') observability.flush_metrics() print(health.readiness(), health.liveness()) PY
    
- Expect: True/False per policy, redacted token, metrics JSON printed, health OK.
    

---

## **Phase 3 — Fetch Layer (offline‑first)**

  

**Why:** standard interface for content retrieval, even for fixture files.

  

**Files to implement**

- pipeline_core/fetch/backoff.py:
    
    - should_retry(status:int)->bool (429/5xx), next_sleep(retry:int)->float (exp backoff with jitter).
        
    
- pipeline_core/fetch/rate_limit.py:
    
    - Simple token bucket (global), acquire() non‑blocking + sleep.
        
    
- pipeline_core/fetch/cache.py:
    
    - No‑op stubs returning (None, None) for etag/lastmod (wire later).
        
    
- pipeline_core/fetch/client.py:
    
    - get_text(url, *, use_fixture=False, fixture_path=None)->(status, text).
        
    - If use_fixture=True, open file and return (200, <html).
        
    - Else real HTTP with backoff/rate limit (kept but **disabled** in dev profile default).
        
    
- pipeline_core/fetch/headless.py: placeholder class raising NotImplementedError (future feature flag).
    

  

**Smoke test**

- python -
    
- Expect: 200 True.
    

---

## **Phase 4 — Parse (directory page → raw items)**

  

**Why:** convert HTML to raw category/subcategory/all‑in links.

  

**Files to implement**

- pipeline_core/parse/selectors.py:
    
    - Define CSS selectors for: category blocks, subcategory labels, “All in …” anchors.
        
    - Provide primary + fallbacks list.
        
    
- pipeline_core/parse/directory_parser.py:
    
    - parse_directory(html:str)->list[dict] returning items like {type:'category'|'subcategory'|'all_in', name:'SEO', href:'/seo', parent:'Advertising & Marketing'}.
        
    

  

**Smoke test**

- python - <<'PY' from pathlib import Path from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory html = Path('tools/taxonomy_builder/data/clutch_directory.html').read_text() items = parse_directory(html) print('items:', len(items), 'first:', items[0] if items else None) PY
    
- Expect: non‑zero items; sample structure printed.
    

---

## **Phase 5 — Normalize (text/urls/types/lineage)**

  

**Why:** canonicalize names and URLs, tag items, and attach ancestry.

  

**Files to implement**

- pipeline_core/normalize/text.py: clean(s), slugify(s) (lowercase, dashes, ascii safe).
    
- pipeline_core/normalize/urls.py: canonicalize(base, href) → absolute, strip tracking.
    
- pipeline_core/normalize/types.py: small enum helpers; is_all_in(name, href).
    
- pipeline_core/normalize/lineage.py:
    
    - attach_lineage(items)->list[dict] linking children to parents and computing stable IDs {id, parent_id, type, name, slug, url}.
        
    

  

**Smoke test**

- python - <<'PY' from pathlib import Path from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory from tools.taxonomy_builder.pipeline_core.normalize.lineage import attach_lineage from tools.taxonomy_builder.pipeline_core.normalize.text import slugify html = Path('tools/taxonomy_builder/data/clutch_directory.html').read_text() raw = parse_directory(html) norm = attach_lineage(raw) print('norm:', len(norm), 'slug example:', slugify('Social Media Marketing')) PY
    
- Expect: normalized count and a slug like social-media-marketing.
    

---

## **Phase 6 — Assemble & Validate**

  

**Why:** enforce contract and create indexes.

  

**Files to implement**

- pipeline_core/assemble_validate/schema_loader.py:
    
    - Load schema/taxonomy.schema.json (draft‑07).
        
    
- pipeline_core/assemble_validate/validate.py:
    
    - validate_taxonomy(doc) raising on failure.
        
    
- pipeline_core/assemble_validate/dedupe.py:
    
    - Drop dupes by (type, slug, parent_slug).
        
    
- pipeline_core/assemble_validate/index.py:
    
    - Build by_category, by_slug helper maps.
        
    
- schema/taxonomy.schema.json:
    
    - Define version, source, collected_at, items:[{id,type,name,slug,url,parent_id?}].
        
    

  

**Smoke test**

- Tiny driver:
    
    - python - <<'PY' from pathlib import Path from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory from tools.taxonomy_builder.pipeline_core.normalize.lineage import attach_lineage from tools.taxonomy_builder.pipeline_core.assemble_validate.validate import validate_taxonomy html = Path('tools/taxonomy_builder/data/clutch_directory.html').read_text() items = attach_lineage(parse_directory(html)) doc = {'version':'0.1.0','source':'fixture','collected_at':'2025-01-01T00:00:00Z','items':items} validate_taxonomy(doc) print('validated') PY
        
    
- Expect: validated printed.
    

---

## **Phase 7 — Output Writers**

  

**Why:** persist results and optional helper files.

  

**Files to implement**

- pipeline_core/output/provenance.py: stamp source, run_id, parser_version.
    
- pipeline_core/output/writer.py: atomic write to ./data/taxonomy.json.
    
- pipeline_core/output/choices.py: write choices.json (top‑level categories + sub lists).
    
- pipeline_core/output/deadletter.py: append JSONL for failures.
    

  

**Smoke test**

- python - <<'PY' from pathlib import Path from tools.taxonomy_builder.pipeline_core.parse.directory_parser import parse_directory from tools.taxonomy_builder.pipeline_core.normalize.lineage import attach_lineage from tools.taxonomy_builder.pipeline_core.output.writer import write_json items = attach_lineage(parse_directory(Path('tools/taxonomy_builder/data/clutch_directory.html').read_text())) write_json({'version':'0.1.0','source':'fixture','collected_at':'2025-01-01T00:00:00Z','items':items}, 'data/taxonomy.json') print('wrote') PY
    
- Expect: data/taxonomy.json exists.
    

---

## **Phase 8 — Runner Orchestration**

  

**Why:** glue everything into one executable path for the CLI.

  

**Files to implement**

- runtime_delivery/runner.py:
    
    - Resolve profile; set policies & metrics.
        
    - Fetch HTML (fixture path from --html).
        
    - Parse → Normalize → Dedupe → Assemble doc → Validate.
        
    - Add provenance → Write outputs → Flush metrics.
        
    - Return exit code 0/2 accordingly.
        
    

  

**Smoke test**

- python -m tools.taxonomy_builder build --html tools/taxonomy_builder/data/clutch_directory.html --out ./data/taxonomy.json
    
- Expect: exit 0; file written; metrics printed.
    

---

## **Phase 9 — Tests**

  

**Why:** lock behavior with fixtures before live crawling exists.

  

**Files to implement**

- tests/tools/taxonomy_builder/unit/test_text.py (slugify, clean)
    
- tests/tools/taxonomy_builder/unit/test_urls.py (canonicalize)
    
- tests/tools/taxonomy_builder/unit/test_backoff.py
    
- tests/tools/taxonomy_builder/parser/test_directory_parser.py (counts, presence of specific labels)
    
- tests/tools/taxonomy_builder/integration/test_runner_fixture.py (end‑to‑end with fixture)
    
- tests/tools/taxonomy_builder/smoke/test_smoke_fixture.py (file exists, non‑empty items)
    

  

**Smoke test**

- pytest -q tests/tools/taxonomy_builder
    

---

## **Phase 10 — DX & Makefile polish**

  

**Why:** one‑liners for common flows; consistent outputs.

  

**Files to implement**

- Makefile targets:
    
    - init, smoke, test, build-fixture, clean.
        
    

  

**Smoke test**

- make smoke → should build taxonomy from fixture and validate.
    

---

## **Phase 11 — (Optional) Live Fetch Track**

  

**Why:** prepare for real website runs later without breaking fixture flow.

  

**Files to extend**

- Enable client.get_text() network path behind profile == 'prod'.
    
- Add governance.robots_fetch(url) if you choose to respect robots in prod.
    
- Add headless.fetch_rendered(url) behind --use-headless.
    

  

**Smoke test**

- Keep using fixture in CI. Add a manual prod runbook when you’re ready.
    

---

## **Run order recap (single command once Phases 0–8 complete)**

```
cd Build/src
python -m tools.taxonomy_builder build \
  --profile dev \
  --html tools/taxonomy_builder/data/clutch_directory.html \
  --out ./data/taxonomy.json
```

**Success criteria:**

- data/taxonomy.json exists, passes schema validation, contains categories, subcategories, and “All in …” links with lineage and slugs.
    
- Metrics printed; exit code 0.