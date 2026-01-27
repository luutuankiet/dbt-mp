# Coding Conventions

**Analysis Date:** 2026-01-27

## Naming Patterns

**Files:**
- Python files use `snake_case` (e.g., `main.py`).

**Functions:**
- Functions use `snake_case` (e.g., `run_dbt_ls`, `slim_node`).

**Variables:**
- Variables use `snake_case` (e.g., `select_statement`, `manifest_path`).

**Types:**
- Not applicable. The codebase does not use type hinting extensively beyond basic types in function signatures.

## Code Style

**Formatting:**
- No automated formatting tool (like Black or Ruff) is detected in `pyproject.toml`.
- The style is generally consistent with PEP 8, but not strictly enforced.
- Indentation is 4 spaces.
- Maximum line length is not strictly enforced but generally stays within a reasonable limit.

**Linting:**
- No linting tool (like Flake8 or Pylint) is detected in `pyproject.toml`.

## Import Organization

**Order:**
- Imports are grouped at the top of the file.
- The observed order is:
    1. Standard library modules (`argparse`, `json`, `subprocess`, `sys`, `logging`)

**Path Aliases:**
- No path aliases are used. All imports are direct.

## Error Handling

**Patterns:**
- Errors are handled using `try...except` blocks.
- Specific exceptions like `FileNotFoundError`, `subprocess.CalledProcessError`, and `json.JSONDecodeError` are caught.
- When an error is caught, a descriptive message is printed to `sys.stderr`.
- The application exits with a non-zero status code (`sys.exit(1)`) upon critical failure.

**Example from `dbt_mp/main.py`:**
```python
    try:
        with open(args.manifest_path, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at '{args.manifest_path}'", file=sys.stderr)
        print("Please run 'dbt compile' or another dbt command to generate it.", file=sys.stderr)
        sys.exit(1)
```

## Logging

**Framework:**
- The `logging` module is imported but not used.
- Informational messages and errors are printed directly to `stdout` or `stderr` using `print()`.

**Patterns:**
- `print()` is used for status updates to the user (e.g., "Compiling models...", "Successfully wrote...").
- `print(..., file=sys.stderr)` is used for error messages.

## Comments

**When to Comment:**
- Comments are not used inline.
- Docstrings are used to explain the purpose of functions.

**Docstrings:**
- Multi-line docstrings in triple-quotes `"""..."""` are present for all functions.
- They describe the function's purpose and sometimes its return value.

## Function Design

**Size:**
- Functions are generally small and focused on a single responsibility. `main()` is the largest function, orchestrating the overall logic.

**Parameters:**
- Function parameters are clearly named.
- Type hints are used for some function parameters (e.g., `select_statement: str`).

**Return Values:**
- Functions have clear return values (e.g., a list of strings, a dictionary). The return types are not explicitly hinted.

## Module Design

**Exports:**
- The `dbt_mp/main.py` file defines several functions, but only `main()` is exposed as a script entry point in `pyproject.toml`.

**Barrel Files:**
- Not applicable to this Python project structure.

---

*Convention analysis: 2026-01-27*
