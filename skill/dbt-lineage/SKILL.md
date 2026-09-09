---
name: dbt-lineage
description: Progressive-disclosure lineage for dbt projects. Generates a slim manifest, orients the agent on the project graph, enables targeted queries into specific models, and guides diagnostic SQL against the warehouse. Use when entering a dbt project to understand lineage, trace data issues, or scope impact of changes.
metadata:
  verified: "2026-09-09"
---

# dbt-lineage

One skill, four stages. Each stage loads only what the current task needs —
never the full manifest. The agent picks the right entry point based on context.

## 0. Schema load — always first

Before anything else, load the self-describing header from the slim manifest.
It contains the schema definitions, jq guardrails, jq recipes, warehouse query
guidance, and resource counts.

```bash
jq '."$manifest_schema"' target/manifest_slim.json
```

Read the output. It is the authoritative guide to every jq command you will
write against this manifest. Obey its guardrails — especially null-safety and
the instruction to never dump whole node objects.

If `target/manifest_slim.json` does not exist, generate it first (§1 below).
If it exists, check its `source_manifest.generated_at` timestamp and tell the
user how old it is before proceeding.

## 1. Generate — produce the slim manifest

Run once per project. The output persists across sessions in
`target/manifest_slim.json`.

**When you have a manifest.json already** (most common — local dbt project or
artifact from a CI/CD fetch):

```bash
uvx dbt-mp --offline --manifest-path <path-to-manifest.json> --out-file target/manifest_slim.json
```

**When you need to compile first** (inside a dbt project with warehouse access):

```bash
uvx dbt-mp --manifest-path target/manifest.json --out-file target/manifest_slim.json
```

If `uv` is not available, tell the user: "`uv` is required to run dbt-mp.
Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh`."

**If no manifest.json exists and this project connects to dbt Cloud**, the user
can fetch production artifacts using the dbtcx plugin (`uvx dbtcx fetch-run
<run_id>`), which deposits a full manifest at
`artifacts/run_<id>/manifest.json`. Then run the offline command above against
that path.

## 2. Orient — understand the project shape

Run the orient script to produce a compact index of every model, source, and
macro in the project. This is the "table of contents" — no SQL, no columns,
just the graph structure.

```bash
<this skill's base directory>/scripts/orient.sh target/manifest_slim.json
```

The output is a markdown table with: `name`, `resource_type`, `materialized`,
`relation_name`, `depends_on` (direct parents), `tags`, and `column_count`
(number of documented columns, if any).

**When to use the full Orient:**
- Deep lineage investigation (tracing NULLs, impact analysis, debugging)
- Project onboarding ("help me understand this project")

**When to skip Orient and go straight to Query:**
- Ad-hoc model question ("what does model X depend on?")
- You already know which model to inspect

For ad-hoc questions, use the jq recipes from §0 directly — no need to load
the full index.

## 3. Query — zoom into a specific model

Extract full detail for one model and its upstream/downstream neighbourhood.

```bash
<this skill's base directory>/scripts/query.sh target/manifest_slim.json <unique_id_or_model_name> [depth]
```

- `unique_id_or_model_name`: either the full `model.project.name` unique_id or
  just the model name (the script searches for a match).
- `depth` (optional, default 1): how many hops upstream/downstream to include.

The output includes: compiled SQL, raw SQL, config, columns (when available),
all upstream and downstream models within the requested depth, and the macro
bodies referenced by those models.

Use this when you need to understand a specific transformation, trace a column
through the DAG, or prepare diagnostic SQL.

## 4. Diagnose — run SQL against the warehouse

After identifying a suspect model via Orient + Query, write diagnostic SQL to
confirm the issue. Use the `relation_name` from the model's detail — it is
already fully qualified and quoted for the target warehouse.

**Pattern: NULL attribution** — when a column is NULL downstream but not
upstream, test each hop:

```sql
-- Replace <relation_name> with the model's relation_name from the Query output.
-- Walk upstream: if this returns rows, the NULL originates here or upstream.
SELECT *
FROM <upstream_relation_name>
WHERE <column_name> IS NULL
LIMIT 100
```

**Pattern: row count divergence** — when downstream has fewer/more rows than
expected:

```sql
SELECT COUNT(*) FROM <upstream_relation_name>
-- vs
SELECT COUNT(*) FROM <downstream_relation_name>
```

**Pattern: join fanout** — when a JOIN introduces duplicates or NULLs:

```sql
SELECT
  a.<join_key>,
  COUNT(*) as row_count
FROM <model_relation_name> a
LEFT JOIN <joined_relation_name> b
  ON a.<join_key> = b.<join_key>
GROUP BY 1
HAVING COUNT(*) > 1
```

To execute these queries, find the appropriate credential and query tool
available in your environment. On hosts with credential management skills,
invoke those first to establish the right project and identity before querying.

## Workflow summary

```
Schema load (3k tokens, always)
    │
    ├─── Ad-hoc question ──→ jq recipe from §0 ──→ done
    │
    └─── Deep investigation
              │
              ├── Orient (~20-30k tokens) ──→ identify suspect models
              │
              ├── Query (per-model) ──→ read compiled SQL, trace columns
              │
              └── Diagnose ──→ write + run warehouse SQL ──→ confirm root cause
```
