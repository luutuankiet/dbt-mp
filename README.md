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

### Offline mode (slim a downloaded prod manifest)

If you already have a `manifest.json` (for example, one downloaded from your production dbt run), you don't need a working dbt project, a warehouse connection, or to run `dbt compile`/`dbt ls` at all — everything (`compiled_code`, `relation_name`, dependencies, and the lineage graph) is already baked into the manifest. Pass `--offline` to slice it directly:

```bash
dbt-mp --offline --manifest-path prod_manifest.json --select '+stg_orders+' --out-file slim_manifest.json
```

In offline mode, selection is resolved from the manifest's own `parent_map`/`child_map`, supporting the common graph operators: `model`, `+model`, `model+`, `+model+`, `N+model` (ancestors up to N edges), and `model+N` (descendants up to N edges). Multiple selectors separated by whitespace are unioned. Omitting `--select` slims the entire manifest. (Method selectors like `tag:` / `path:` and set operators are only available on the live dbt path.)

Because the prod manifest carries the real `relation_name` for every node and source, the slimmed output tells an agent the exact fully-qualified warehouse table to query in production.

### Querying the output with `jq`

Every output file embeds a self-describing `$manifest_schema` block at the top. Beyond the JSON schema for each resource, it now includes:

- `source_manifest` — provenance of the manifest the slice was parsed from (`dbt_version`, `adapter_type`, `project_name`, ...).
- `selection_used` — the `--select` string that produced the slice.
- `resource_counts` — aggregate cardinality per resource type (e.g. `{"test": 746, "model": 407, ...}`), so an agent knows the shape of the slice — and that tests usually dominate — before writing any query.
- `structure` / `querying_the_warehouse` — plain-English notes on how the file is laid out and how to turn a model into a real warehouse query (use `relation_name` verbatim).
- `jq_guardrails` — the failure modes to avoid: guard missing keys with `// {}` / `// []`, filter to models before lineage walks, project single fields instead of dumping whole nodes.
- `jq_recipes` — ready-to-run, null-safe `jq` snippets for the questions agents ask most, e.g. *"what exact deps does this model depend on?"*:

```bash
# Direct upstream deps (models + sources) of a model
jq '.nodes["model.project.stg_orders"].depends_on.nodes // []' slim_manifest.json

# Those deps, resolved to the warehouse relation you'd actually query
jq -r '(.nodes["model.project.stg_orders"].depends_on.nodes // [])[] as $d
        | ((.nodes[$d] // .sources[$d] // {}).relation_name // $d)' slim_manifest.json

# Reverse lineage: which models depend directly on a given node (skips tests)
jq '.nodes | to_entries
    | map(select(.value.resource_type == "model"
                 and ((.value.depends_on.nodes // []) | index("model.project.raw_orders"))))
    | map(.key)' slim_manifest.json
```

`$dbt_ls_selection` — the full list of selected unique_ids, tests included — deliberately stays at the root rather than inside `$manifest_schema`, since it can run to hundreds of entries.

### dbt executable resolution

On the live path (non-`--offline`), `dbt-mp` locates the dbt CLI automatically, preferring a project virtualenv in the current directory (`./.venv` or `./venv`) before falling back to an active `VIRTUAL_ENV` and then `dbt` on your `PATH`. This means `uvx dbt-mp ...` works from a dbt project root even if you forgot to `source .venv/bin/activate`. The chosen executable is printed at the start of the run.

### Manifest version tolerance

`dbt-mp` is intentionally **not** pinned to a manifest schema version. It reads a small set of stable, high-signal keys defensively, so a newer or older `manifest.json` degrades gracefully (missing keys are simply omitted) rather than breaking. Every output echoes the source manifest's provenance under `$manifest_schema.source_manifest` (`dbt_version`, `dbt_schema_version`, `adapter_type`, `project_name`, `generated_at`) so any version mismatch is visible to the consuming agent rather than silent.

---

## Core Attributes for Contextual Quality

`dbt-mp` optimizes the manifest by preserving a curated set of high-signal attributes that balance context quality with token economy. The following keys are retained:

### `nodes`

| Attribute                         | Rationale                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------- |
| `schema`, `name`, `resource_type` | Basic identifiers for the node.                                                             |
| `unique_id`                       | The canonical, unique identifier within the dbt graph.                                      |
| `relation_name`                   | The fully-qualified, quoted warehouse relation (e.g. `"db"."schema"."table"`) — the exact identifier to put in a `FROM` clause to query this model. |
| `config` (subset)                 | Key configuration like `materialized` and `enabled` are crucial for understanding behavior. |
| `tags`                            | Metadata for selection/organization.                                                        |
| `columns`                         | Per-column `name`/`description`/`data_type` (when documented) — the model's output schema. Omitted when the model has no documented columns. |
| `raw_code`, `compiled_code`       | The original and compiled SQL are the most critical assets for code analysis.               |
| `refs`, `sources`, `depends_on`   | The explicit dependency graph is fundamental for lineage tracing.                           |

### `sources`

| Attribute                    | Rationale                                        |
| ---------------------------- | ------------------------------------------------ |
| `database`, `schema`, `name` | Identifiers for the source table.                |
| `unique_id`                  | The canonical identifier for the source.         |
| `relation_name`              | The fully-qualified, quoted warehouse relation to query this source. |
| `description`                | Semantic context for what the source represents. |
| `columns`                    | Per-column `name`/`description`/`data_type` (when documented) — so an agent can see what the source table emits. |

### `macros`

| Attribute   | Rationale                                                       |
| ----------- | --------------------------------------------------------------- |
| `unique_id` | The canonical identifier for the macro.                         |
| `macro_sql` | The macro's code is essential, as it's injected into model SQL. |

---
 
