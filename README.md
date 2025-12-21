# dbt Manifest Parser (`dbt-mp`)

**A focused, lightweight CLI tool for parsing and filtering dbt `manifest.json` files to create context-optimized artifacts for AI agents and developer onboarding.**

---

## Why This Exists

Navigating large, complex dbt projects with hundreds of models can be a significant challenge. While dbt's lineage is powerful at the model level, understanding the intricate dependencies within deeply nested CTEs often requires manual, time-consuming code tracing. This complexity creates a major hurdle for both onboarding new developers and for leveraging AI agents to assist with code analysis, as the full `manifest.json` file is often too large and noisy for effective use in LLM contexts.

`dbt-mp` was built to solve this problem. It bridges the gap between the high-level view of `dbt ls` and the overwhelming detail of the full manifest. By intelligently selecting a target model and its direct lineage, and then filtering the manifest to include only the most critical attributes, it generates a concise, token-optimized JSON artifact.

**The goal:** To make interacting with large dbt projects more efficient for both humans and AI, accelerating development, and simplifying the process of understanding complex data transformations.

---

## What It Does

`dbt-mp` is a command-line tool that performs a two-step process:

1. **Select & Compile**: It first invokes `dbt ls` with your specified model selector (e.g., `+my_model`) to compile your project and generate a fresh `manifest.json`. This ensures the artifact is always up-to-date with your current code.
2. **Parse & Filter**: It then parses the newly generated manifest, extracting only the selected models, their direct parents, and any associated macros. It intelligently slims down the JSON, keeping high-signal attributes while discarding less relevant data to optimize for token count.

This produces a hyper-focused JSON file, perfect for:

- Providing as context to an AI agent for code refactoring or analysis.
- Including in a Pull Request to give reviewers a clear picture of the changes.
- Speeding up the onboarding process for developers new to the project.

---

## Benchmark: Performance & Token Reduction

To demonstrate the effectiveness of `dbt-mp`, we ran it on the standard [dbt Labs' `jaffle_shop` project](https://github.com/dbt-labs/jaffle-shop), which contains approximately 20 models. The results show a significant reduction in the size of the manifest, making it far more suitable for AI agent contexts.

| Metric     | Raw `manifest.json` | `dbt-mp` Slim Manifest | Reduction |
| ---------- | ------------------- | ---------------------- | --------- |
| **Tokens** | ~343,000            | ~8,800                 | **~97%**  |
| **Lines**  | ~21,000             | ~450                   | **~98%**  |

This dramatic decrease in size allows for a much more focused and efficient analysis by both developers and LLM-based tools.

---

## Installation

The tool is packaged and distributed via PyPI.

```bash
# Via pip
pip install dbt-mp

# Or run as a one-off executable via uv
uvx dbt-mp --help
```

---

## Usage

To use the tool, run the `dbt-mp` command from the root of your dbt project directory. The most common use case is to provide a dbt model selector and an output file path.

**Example:**

The following command will select the model `stg_orders`, its parents (`+`), and its children (`+`), then generate a filtered manifest.

```bash
dbt-mp --select '+stg_orders+' --out-file filtered_manifest.json
```

The resulting `slim_manifest.json` will contain a lean, context-rich representation of the selected slice of your dbt project.

---

## Core Attributes for Contextual Quality

`dbt-mp` optimizes the manifest by preserving a curated set of high-signal attributes that balance context quality with token economy. The following keys are retained:

### `nodes`

| Attribute                         | Rationale                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------- |
| `schema`, `name`, `resource_type` | Basic identifiers for the node.                                                             |
| `unique_id`                       | The canonical, unique identifier within the dbt graph.                                      |
| `config` (subset)                 | Key configuration like `materialized` and `enabled` are crucial for understanding behavior. |
| `tags`, `columns`                 | Metadata and column-level descriptions provide essential semantic context.                  |
| `raw_code`, `compiled_code`       | The original and compiled SQL are the most critical assets for code analysis.               |
| `refs`, `sources`, `depends_on`   | The explicit dependency graph is fundamental for lineage tracing.                           |

### `sources`

| Attribute                    | Rationale                                        |
| ---------------------------- | ------------------------------------------------ |
| `database`, `schema`, `name` | Identifiers for the source table.                |
| `unique_id`                  | The canonical identifier for the source.         |
| `description`                | Semantic context for what the source represents. |

### `macros`

| Attribute   | Rationale                                                       |
| ----------- | --------------------------------------------------------------- |
| `unique_id` | The canonical identifier for the macro.                         |
| `macro_sql` | The macro's code is essential, as it's injected into model SQL. |

---
