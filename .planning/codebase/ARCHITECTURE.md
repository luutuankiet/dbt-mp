# Architecture

**Analysis Date:** 2026-01-27

## Pattern Overview

**Overall:** Procedural CLI Script

This tool is a command-line interface (CLI) application built in Python. It follows a simple procedural pattern orchestrated from the `main` function in `dbt_mp/main.py`. The architecture is not based on a framework like MVC or MVT, but is a straightforward script that executes a sequence of operations.

**Key Characteristics:**
- **Single Entry Point:** The application is invoked as a script via the `dbt-mp` command, which calls the `main` function.
- **External Process Dependency:** Core logic relies on shelling out to the `dbt` command-line tool using Python's `subprocess` module to compile and list dbt resources.
- **File I/O Driven:** The application's primary purpose is to read a large JSON file (`manifest.json`), process its contents in memory, and write a smaller, filtered JSON file.

## Layers

**Orchestration Layer:**
- Purpose: Manages the application lifecycle, parses command-line arguments, and calls other functions in the correct sequence.
- Location: `dbt_mp/main.py`
- Contains: The `main()` function.
- Depends on: All other functions (`run_dbt_ls`, `slim_node`, etc.).

**dbt Interaction Layer:**
- Purpose: Interacts with the external `dbt` CLI to generate necessary artifacts and gather information about the dbt project.
- Location: `dbt_mp/main.py`
- Contains: The `run_dbt_ls()` function and `subprocess` calls within `main()`.
- Used by: The Orchestration Layer (`main()`).

**Data Processing Layer:**
- Purpose: Filters and transforms the manifest data according to the selection criteria.
- Location: `dbt_mp/main.py`
- Contains: The `slim_node()`, `slim_source()`, and `slim_macro()` functions, along with the dictionary filtering logic inside `main()`.
- Used by: The Orchestration Layer (`main()`).

## Data Flow

**Manifest Slimming Process:**

1.  The user executes the script via the `dbt-mp` command, providing a dbt selection string (e.g., `--select my_model+`).
2.  The `main` function parses the CLI arguments.
3.  The script executes `dbt compile` to ensure the `manifest.json` is up-to-date.
4.  The script executes `dbt ls` with the user's selection to get a list of unique IDs for the selected resources (models, sources).
5.  The full `target/manifest.json` file is loaded into a Python dictionary.
6.  The script identifies all macros that the selected resources depend on by inspecting the `depends_on` key in the manifest.
7.  A final set of unique IDs is created, combining the selected resources and their dependent macros.
8.  The script iterates through the nodes, sources, and macros in the full manifest dictionary. If an item's unique ID is in the final set, it is processed.
9.  Each selected item is passed to a `slim_*` function (`slim_node`, `slim_source`, `slim_macro`) which creates a new, smaller dictionary containing only a predefined set of essential key-value pairs.
10. The slimmed-down items are collected into a final `slim_manifest` dictionary.
11. This `slim_manifest` dictionary is written to a new JSON file (e.g., `manifest_slim.json`).

## Key Abstractions

**Manifest Subset:**
- Purpose: The core concept is creating a subset of the dbt manifest. The `slim_manifest` dictionary is the primary data structure that represents this abstraction.
- Examples: The `slim_manifest` variable in `dbt_mp/main.py`.
- Pattern: A nested dictionary with keys `nodes`, `sources`, and `macros`.

**Slimmed Resource:**
- Purpose: To represent a dbt resource (node, source, or macro) with a reduced set of attributes, making it smaller and easier to consume.
- Examples: The dictionaries returned by `slim_node()`, `slim_source()`, and `slim_macro()`.
- Pattern: Simple dictionary creation, selecting specific keys from the larger source dictionary.

## Entry Points

**CLI Script:**
- Location: `dbt_mp/main.py`
- Triggers: Executing `dbt-mp` from the command line. This is configured in `pyproject.toml` under `[project.scripts]`.
- Responsibilities: To orchestrate the entire manifest parsing and slimming process from end to end.

## Error Handling

**Strategy:** The application uses `try...except` blocks to handle expected errors gracefully.

**Patterns:**
- **File Not Found:** Catches `FileNotFoundError` when `target/manifest.json` is missing and prints a user-friendly message explaining how to generate it.
- **External Command Failure:** Catches `subprocess.CalledProcessError` if a `dbt` command fails, printing the error and stderr to the console.
- **JSON Decoding:** Catches `json.JSONDecodeError` for malformed JSON in `manifest.json` or the `dbt ls` output.
- **Exiting:** Upon catching an error, a message is printed to `sys.stderr` and the application exits with a non-zero status code using `sys.exit(1)`.

## Cross-Cutting Concerns

**Logging:** Standard library `logging` is imported but not used. Status messages and errors are printed directly to `stdout` and `stderr` using `print()`.
**Validation:** Command-line arguments are defined and implicitly validated by `argparse`. There is no further data validation.
**Authentication:** Not applicable. The tool interacts with the local filesystem and local `dbt` installation.

---

*Architecture analysis: 2026-01-27*
