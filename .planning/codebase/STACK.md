# Technology Stack

**Analysis Date:** 2026-01-27

## Languages

**Primary:**
- Python >=3.10 - Used for all application logic.

## Runtime

**Environment:**
- Python - The core runtime for the application.
- dbt CLI - An external command-line tool dependency that must be present in the execution environment's PATH. The application interacts with it via `subprocess` calls.

**Package Manager:**
- uv - Indicated by the presence of `uv.lock`.
- Lockfile: present (`uv.lock`)

## Frameworks

**Core:**
- None. The application is a script using standard libraries.

**CLI:**
- `argparse` - Used for parsing command-line arguments.

## Key Dependencies

**Direct:**
- `python-semantic-release>=10.5.3` - Used for automating versioning and releases, primarily a development/CI dependency.

**Standard Library:**
- `json` - For reading and writing manifest files.
- `subprocess` - For executing `dbt` commands.
- `argparse` - For building the CLI interface.

## Configuration

**Environment:**
- Configuration is provided exclusively through command-line arguments. No `.env` or other environment configuration files were detected.

**Build:**
- `pyproject.toml` - Defines project metadata, dependencies, and entry points.

## Platform Requirements

**Development:**
- Python >=3.10
- uv package manager
- dbt CLI installed and in PATH

**Production:**
- The application is a CLI tool, intended to be run in an environment where Python and the dbt CLI are available.

---

*Stack analysis: 2026-01-27*
