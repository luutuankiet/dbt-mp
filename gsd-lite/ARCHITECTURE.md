# Architecture

*Mapped: 2026-02-07*

## Project Structure Overview

| Directory | Purpose |
|-----------|---------|
| `dbt_mp/` | Main application package containing source code |
| `pyproject.toml` | Project configuration, dependencies, and CLI entry point definition |
| `uv.lock` | Dependency lockfile |

## Tech Stack

- **Runtime:** Python >=3.10
- **Language:** Python
- **Key Dependencies:**
  - `dbt` CLI - External runtime requirement; accessed via `subprocess` calls
  - `python-semantic-release` - Automated versioning and release management
  - `uv` - Python package manager

## Data Flow

0. Prerequisite : user cwd must be in an active dbt project and dbt venv is active
1. User executes `dbt-mp` CLI with selection arguments (e.g., `--select my_model+`)
2. `main()` parses arguments and orchestrates the process
3. Script executes `dbt compile` to ensure fresh artifacts
4. Script executes `dbt ls` to identify selected resources
5. `target/manifest.json` is loaded into memory
6. Core logic filters nodes, sources, and macros based on selection and dependencies
7. Slimmed data structure is written to output JSON file (default: `manifest_slim.json`)

## Entry Points

Start reading here:

- `dbt_mp/main.py` - **The Core:** Contains the `main()` entry point, CLI argument parsing, and all manifest processing logic.
- `pyproject.toml` - Defines the `dbt-mp` console script and project metadata.
- `README.md` - Usage instructions and setup.
