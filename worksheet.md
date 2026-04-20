# genaikeys — GA Readiness Worksheet

> Action plan to bring **genaikeys** to the same open-source standard as
> [rihoneailabs/llmcall](https://github.com/rihoneailabs/llmcall).
>
> Generated: 2026-04-20 · Branch: `claude/review-ga-readiness-6Oadt`

---

## Current State Summary

| Area | Status | Notes |
|------|--------|-------|
| **API / Code** | ✅ Solid | Clean singleton + plugin arch, thread-safe, no credential leakage |
| **Tests** | ✅ Good | Unit + e2e, mocks cloud SDKs, covers caching/TTL/thread safety |
| **CI** | ⚠️ Partial | pytest + ruff check run; no ruff format, no mypy, no dependabot |
| **Packaging** | ⚠️ Partial | Poetry-based with extras; still v0.1.0, no `poetry.toml` |
| **Community files** | ❌ Gaps | Missing SECURITY.md, CODE_OF_CONDUCT, issue/PR templates, CODEOWNERS |
| **Dev tooling** | ❌ Missing | No pre-commit, no VS Code settings, no tox |
| **Docs** | ⚠️ README-only | No `docs/` folder; README is comprehensive but monolithic |

---

## Phase 1 — Community & Legal Files

- [ ] **1.1** Create `SECURITY.md` — responsible disclosure policy (referenced in CONTRIBUTING.md but missing)
- [ ] **1.2** Create `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- [ ] **1.3** Create `.github/pull_request_template.md`
- [ ] **1.4** Create `.github/ISSUE_TEMPLATE/bug_report.md`
- [ ] **1.5** Create `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] **1.6** Create `.github/CODEOWNERS`

## Phase 2 — Developer Tooling & DX

- [ ] **2.1** Create `.pre-commit-config.yaml` — ruff lint + format, trailing whitespace, YAML check
- [ ] **2.2** Add `[tool.ruff.format]` config to `pyproject.toml`
- [ ] **2.3** Add mypy dev dependency + `[tool.mypy]` config to `pyproject.toml`
- [ ] **2.4** Create `.vscode/settings.json` — format-on-save, ruff as linter

## Phase 3 — CI/CD Hardening

- [ ] **3.1** Update `.github/workflows/ci.yml` — add `ruff format --check` + mypy steps
- [ ] **3.2** Create `.github/dependabot.yml` — weekly pip updates
- [ ] **3.3** Create `tox.ini` — multi-env runner for Python 3.10/3.11/3.12

## Phase 4 — Docs & Packaging Polish

- [ ] **4.1** Create `docs/index.md` — project overview
- [ ] **4.2** Create `docs/configuration.md` — per-provider auth chain docs
- [ ] **4.3** Create `docs/custom-backends.md` — plugin interface guide
- [ ] **4.4** Create `poetry.toml` — `virtualenvs.in-project = true`
- [ ] **4.5** Bump version `0.1.0` → `1.0.0` in `pyproject.toml`
- [ ] **4.6** Add GA release entry to `CHANGELOG.md`

## Phase 5 — Test Coverage Gaps

- [ ] **5.1** Add error/exception tests (network failure, auth failure)
- [ ] **5.2** Add `--cov-fail-under=80` coverage threshold to `pyproject.toml`
- [ ] **5.3** Create `tests/test_plugin.py` — custom SecretManagerPlugin interface tests

---

## llmcall vs genaikeys Comparison

| Item | llmcall | genaikeys (before) | genaikeys (after) |
|------|---------|--------------------|--------------------|
| SECURITY.md | ✅ | ❌ | ✅ |
| CODE_OF_CONDUCT | ✅ | ❌ | ✅ |
| pre-commit config | ✅ | ❌ | ✅ |
| tox.ini | ✅ | ❌ | ✅ |
| poetry.toml | ✅ | ❌ | ✅ |
| dependabot | ✅ | ❌ | ✅ |
| docs/ folder | ✅ | ❌ | ✅ |
| .vscode settings | ✅ | ❌ | ✅ |
| Issue templates | ✅ | ❌ | ✅ |
| PR template | ✅ | ❌ | ✅ |
| mypy in CI | ✅ | ❌ | ✅ |
| ruff format | ✅ | lint only | ✅ |
| Version ≥1.0 | ✅ | 0.1.0 | 1.0.0 |
| Coverage threshold | ✅ | ❌ | ✅ (80%) |

---

## Verification Checklist

- [ ] `ruff check genaikeys/ && ruff format --check genaikeys/` passes
- [ ] `pytest --cov=genaikeys --cov-fail-under=80` passes
- [ ] `mypy genaikeys/` reports no errors
- [ ] CI workflow runs successfully
- [ ] All new community files render correctly on GitHub

---

## Out of Scope

- Rewriting provider implementations (already secure and clean)
- Adding async support
- PyPI publishing workflow changes (already uses trusted OIDC publishing)
- GitHub repo topics (done via GitHub UI)
