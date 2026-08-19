---
name: dependabot-remediation
description: >-
  Repository-specific skill for discovering, triaging, and remediating Dependabot
  security alerts, CVEs, and supply-chain threats for the genaikeys project
  (Python 3.11-3.13, uv, pytest, ruff, pip-audit).
---

# Dependabot & Supply Chain Security Remediation (genaikeys)

This skill provides an automated, project-tailored workflow for auditing, triaging, and patching GitHub Dependabot alerts, CVEs, and dependency supply-chain risks specifically for the **`genaikeys`** repository (`ndamulelonemakh/genaikeys`).

---

## Project Profile & Toolchain

- **Repository**: `ndamulelonemakh/genaikeys`
- **Supported Runtimes**: Python `3.11`, `3.12`, `3.13`
- **Package & Environment Manager**: `uv`
- **Manifest**: `pyproject.toml` (Build backend: `hatchling`)
- **Lockfile**: `uv.lock`
- **Linter & Formatter**: `ruff`
- **Test Runner & Coverage**: `pytest` + `pytest-cov` (Enforces ≥ 80% coverage threshold)
- **Vulnerability Scanner**: `pip-audit` via `uvx pip-audit`
- **CI Workflows**: `.github/workflows/ci.yml`, `.github/workflows/python-publish.yml`, `.github/dependabot.yml`

---

## When to Activate

Trigger this skill whenever:
- Listing, triaging, auditing, or resolving Dependabot security alerts on `genaikeys`.
- Reviewing or responding to Dependabot PRs (`dependabot/*` branches).
- Upgrading runtime or development dependencies to prevent supply chain tampering.
- Running pre-release or CI dependency vulnerability checks.

---

## Step-by-Step Remediation Workflow

```
1. Fetch Dependabot Alerts (GitHub API)
              │
2. Identify Target Packages & Bump Minimums (pyproject.toml)
              │
3. Regenerate & Sync Lockfile (uv lock --upgrade)
              │
4. Run Security Audit (uvx pip-audit)
              │
5. Run Linter & Test Suite Matrix (ruff + pytest)
              │
6. Commit & Open PR / Verify Alert Closure
```

---

### Step 1: Query Open Dependabot Alerts

Query the GitHub API for active alerts on `ndamulelonemakh/genaikeys`:

```bash
gh api "repos/ndamulelonemakh/genaikeys/dependabot/alerts?state=open&per_page=100" \
  --jq '[.[] | {
    number: .number,
    package: .security_vulnerability.package.name,
    ecosystem: .security_vulnerability.package.ecosystem,
    severity: .security_advisory.severity,
    summary: .security_advisory.summary,
    patched_version: .security_vulnerability.first_patched_version.identifier,
    vulnerable_range: .security_vulnerability.vulnerable_version_range,
    manifest: .dependency.manifest_path
  }]'
```

---

### Step 2: Apply Version Fixes

#### A. Direct Dependencies (`pyproject.toml`)
If the advisory targets a direct dependency (e.g. `cryptography`, `pydantic-settings`, `azure-identity`, `azure-keyvault-secrets`, `boto3`, `google-cloud-secret-manager`), bump the minimum version specifier in `pyproject.toml`:

```toml
[project]
dependencies = [
    "cryptography>=50.0.0",
    "azure-identity>=1.25.0",
    "azure-keyvault-secrets>=4.10.0",
    "pydantic-settings>=2.14.2",
]
```

#### B. Transitive & Lockfile Upgrades (`uv.lock`)
For both direct and transitive vulnerabilities (e.g. `pyjwt`, `pyasn1`, `idna`), upgrade using `uv`:

```bash
# Upgrade a specific package:
uv lock --upgrade-package <package-name>

# Or upgrade all dependencies to latest compatible versions:
uv lock --upgrade

# Synchronize the active environment:
uv sync --all-extras
```

---

### Step 3: Run Full Verification Suite

Always execute all 4 verification pillars before committing changes:

1. **Vulnerability Audit:**
   ```bash
   uvx pip-audit
   ```
   *Must report "No known vulnerabilities found".*

2. **Linter & Formatter Validation:**
   ```bash
   uv run ruff check genaikeys/
   uv run ruff format --check genaikeys/
   ```

3. **Test Suite & Coverage Matrix:**
   ```bash
   uv run pytest --cov=genaikeys --cov-report=term-missing
   ```
   *All tests must pass and code coverage must remain ≥ 80%.*

4. **Lockfile Integrity:**
   ```bash
   uv lock --check
   ```

---

### Step 4: Quarantine & Dev Container Testing

Run dependency updates and tests in full isolation before merging or applying on the host:

#### A. Interactive Quarantine via Dev Container
Open the repository in VS Code / IDE with Remote - Containers:
- Command: `Dev Containers: Reopen in Container`
- Defined in [.devcontainer/devcontainer.json](file:///Users/ndamulelonemakhavhani/projects/opensource/genaikeys/.devcontainer/devcontainer.json) and [.devcontainer/Dockerfile](file:///Users/ndamulelonemakhavhani/projects/opensource/genaikeys/.devcontainer/Dockerfile)
- All build, lockfile, and test commands run under the non-root `vscode` user with host keyring access disabled (`PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring`).

#### B. Headless One-Shot Quarantine Check
When verifying a Dependabot PR or locked bump without opening a GUI session:

```bash
docker build -t genaikeys-quarantine -f .devcontainer/Dockerfile .
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  genaikeys-quarantine bash -c "
    uv sync --all-extras && \
    uvx pip-audit && \
    uv run ruff check genaikeys/ && \
    uv run pytest --cov=genaikeys --cov-report=term-missing
  "
```

---

### Step 5: Git Commit & PR Workflow

1. Create a dedicated branch:
   ```bash
   git checkout -b fix/deps-security-updates
   ```

2. Follow conventional commit standards:
   - Direct runtime dependencies: `fix(deps): bump <package> to >=<version> to resolve <CVE/GHSA>`
   - Development dependencies: `chore(deps-dev): bump <package> to <version>`
   - GitHub Actions: `chore(actions): update <action> to <version>`

3. Create the Pull Request:
   ```bash
   git push -u origin fix/deps-security-updates
   gh pr create \
     --title "fix(deps): bump <packages> to patch security vulnerabilities" \
     --body "Resolves Dependabot security alerts for <packages>."
   ```

4. Verify alert closure post-merge:
   ```bash
   gh api "repos/ndamulelonemakh/genaikeys/dependabot/alerts?state=open"
   ```
