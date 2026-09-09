#!/usr/bin/env bash
set -euo pipefail

# Orient: produce a compact markdown index of every model, source, and macro
# in a slim manifest. No SQL, no columns — just the graph structure.
#
# Usage: orient.sh <path-to-manifest_slim.json>

MANIFEST="${1:?Usage: orient.sh <manifest_slim.json>}"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: manifest not found at '$MANIFEST'" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || { echo "Error: jq is required but not found" >&2; exit 1; }

echo "## Manifest provenance"
echo ""
jq -r '
  ."$manifest_schema".source_manifest
  | "- **project**: \(.project_name // "unknown")\n- **dbt version**: \(.dbt_version // "unknown")\n- **adapter**: \(.adapter_type // "unknown")\n- **generated_at**: \(.generated_at // "unknown")"
' "$MANIFEST"
echo ""

echo "## Resource counts"
echo ""
jq -r '
  ."$manifest_schema".resource_counts
  | "- nodes total: \(.nodes_total)\n- sources: \(.sources)\n- macros: \(.macros)"
  , (
    .nodes_by_resource_type | to_entries[]
    | "  - \(.key): \(.value)"
  )
' "$MANIFEST"
echo ""

echo "## Models"
echo ""
echo "| name | materialized | relation_name | depends_on | tags | col_count |"
echo "|---|---|---|---|---|---|"
jq -r '
  .nodes | to_entries[]
  | select(.value.resource_type == "model")
  | .value
  | [
      .name,
      (.config.materialized // "-"),
      (.relation_name // "-"),
      ((.depends_on.nodes // []) | map(split(".")[-1]) | join(", ")),
      ((.tags // []) | join(", ")),
      (if .columns then (.columns | length | tostring) else "-" end)
    ]
  | "| \(.[0]) | \(.[1]) | \(.[2]) | \(.[3]) | \(.[4]) | \(.[5]) |"
' "$MANIFEST"
echo ""

echo "## Sources"
echo ""
echo "| name | unique_id | relation_name | description | col_count |"
echo "|---|---|---|---|---|"
jq -r '
  .sources | to_entries[]
  | .value
  | [
      .name,
      .unique_id,
      (.relation_name // "-"),
      ((.description // "-") | if length > 60 then .[:57] + "..." else . end),
      (if .columns then (.columns | length | tostring) else "-" end)
    ]
  | "| \(.[0]) | \(.[1]) | \(.[2]) | \(.[3]) | \(.[4]) |"
' "$MANIFEST"
echo ""

echo "## Macros"
echo ""
echo "| unique_id | size_chars | body |"
echo "|---|---|---|"
jq -r '
  .macros | to_entries[]
  | .value
  | [
      .unique_id,
      (.macro_sql | length | tostring),
      (if (.macro_sql | length) <= 500
       then (.macro_sql | gsub("\n"; " ") | gsub("\\|"; "\\\\|"))
       else "(large — use query.sh to inspect)"
       end)
    ]
  | "| \(.[0]) | \(.[1]) | \(.[2]) |"
' "$MANIFEST"
