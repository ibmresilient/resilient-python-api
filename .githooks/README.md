# Git Hooks for resilient-python-api

This directory contains git hooks for the resilient-python-api repository.

## Setup

To enable these hooks, run the following command from the repository root:

```bash
git config core.hooksPath .githooks
```

This tells Git to use hooks from `.githooks/` instead of the default `.git/hooks/` directory.

**Note:** This configuration is local to each repository clone and must be set by each developer.

## Available Hooks

### commit-msg

**Purpose:** Validates commit message format to ensure it includes a JIRA ticket number.

**Requirements:**
- Commit messages must include a JIRA ticket in format: `SOARAPPS-####` or `INT-####`
- OR start with `Merge` for merge commits

**Valid examples:**
```
✅ SOARAPPS-9569 {resilient} add explicit version variables
✅ INT-123 fix bug in resilient-lib
✅ Merge branch 'master' into story/SOARAPPS-9569
```

**Invalid examples:**
```
❌ added new feature (missing ticket number)
❌ fix bug (missing ticket number)
```

**Related:** See SOARAPPS-9524 for regex pattern fix details.

---

### pre-commit

**Purpose:** Validates branch names and runs pre-commit framework (detect-secrets scanning).

**Branch Name Requirements:**
Branch names must follow the format: `type/TICKET-####/package_name/description`

**Valid examples:**
```
✅ story/SOARAPPS-9569/resilient/add-version-variables
✅ bug/INT-123/resilient-lib/fix-unicode-error
✅ task/SOARAPPS-456/resilient-circuits/update-docs
✅ epic/SOARAPPS-789/resilient-sdk
```

**What it does:**
1. Validates branch name format
2. Runs pre-commit framework hooks (detect-secrets, etc.)

**Prerequisites:**
- Install pre-commit framework: `pip install pre-commit`
- The hook will fail if pre-commit is not installed

**Related:** See SOARAPPS-9524 for integration details.

---

### pre-push

**Purpose:** Automatically creates version tags based on `resilient/setup.cfg` before pushing to remote.

**What it does:**
- Runs before every `git push`
- Calls `.scripts/create_version_tag.sh` to check/create version tag
- Reads version from `resilient/setup.cfg`
- Creates tag in format `v{version}` (e.g., `v51.0.8.2`)
- Only creates tag if it doesn't already exist (safe to run multiple times)
- Won't block push if tag creation fails (just warns)

**Benefits:**
- Ensures version tags stay synchronized with setup.cfg versions
- Prevents version mismatches between git tags and PyPI releases
- No manual tag management required

**Related:** See SOARAPPS-9569 for full context on version management improvements.

---

## Documentation

For more information about git hooks in this repository, see:
- [Githooks Documentation](https://github.ibm.com/Resilient/wiki-int/blob/master/docs/Development%20Process/Githooks_Documentation.md)
- [Version Management Documentation](https://github.ibm.com/Resilient/wiki-int/blob/master/docs/CI_CD/VERSION_MANAGEMENT.md)

## Troubleshooting

### Hooks not running

If hooks aren't running, verify the configuration:

```bash
git config core.hooksPath
```

Should output: `.githooks`

If not, run the setup command again:

```bash
git config core.hooksPath .githooks
```

### Permission issues

Ensure hooks are executable:

```bash
chmod +x .githooks/*
```

### pre-commit not found

Install the pre-commit framework:

```bash
pip install pre-commit
```
Ensure githooks is not set as it will complain. Set after installation of pre-commit.

### Version tag script not found

The pre-push hook depends on `.scripts/create_version_tag.sh`. Ensure this file exists and is executable:

```bash
ls -la .scripts/create_version_tag.sh
chmod +x .scripts/create_version_tag.sh
```

## History

- **SOARAPPS-9524** (2026-05-20): Fixed commit-msg regex pattern and integrated pre-commit framework
- **SOARAPPS-9569** (2026-06-23): Added pre-push hook for automatic version tag creation