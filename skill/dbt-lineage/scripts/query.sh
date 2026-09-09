#!/usr/bin/env bash
set -euo pipefail

# Query: extract full detail for a model and its upstream/downstream neighbourhood.
#
# Usage: query.sh <manifest_slim.json> <model_name_or_unique_id> [depth]
#   depth: number of hops upstream/downstream to include (default: 1)

MANIFEST="${1:?Usage: query.sh <manifest_slim.json> <model_name_or_unique_id> [depth]}"
MODEL="${2:?Usage: query.sh <manifest_slim.json> <model_name_or_unique_id> [depth]}"
DEPTH="${3:-1}"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: manifest not found at '$MANIFEST'" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || { echo "Error: jq is required but not found" >&2; exit 1; }

# Resolve model: try exact unique_id first, then search by name
UNIQUE_ID=$(jq -r --arg m "$MODEL" '
  if .nodes[$m] then $m
  else
    .nodes | to_entries[]
    | select(.value.name == $m and .value.resource_type == "model")
    | .key
  end
' "$MANIFEST" | head -1)

if [ -z "$UNIQUE_ID" ] || [ "$UNIQUE_ID" = "null" ]; then
  echo "Error: model '$MODEL' not found in manifest" >&2
  echo "Available models:" >&2
  jq -r '.nodes | to_entries[] | select(.value.resource_type == "model") | .value.name' "$MANIFEST" | sort >&2
  exit 1
fi

echo "## Model: $UNIQUE_ID"
echo ""

# Primary model detail
echo "### Detail"
echo ""
jq --arg id "$UNIQUE_ID" '
  .nodes[$id]
  | {
      name,
      resource_type,
      unique_id,
      relation_name,
      config,
      tags,
      columns,
      depends_on,
      refs,
      sources
    }
' "$MANIFEST"
echo ""

echo "### Raw SQL"
echo '```sql'
jq -r --arg id "$UNIQUE_ID" '.nodes[$id].raw_code // "<<not available>>"' "$MANIFEST"
echo '```'
echo ""

echo "### Compiled SQL"
echo '```sql'
jq -r --arg id "$UNIQUE_ID" '.nodes[$id].compiled_code // "<<not compiled>>"' "$MANIFEST"
echo '```'
echo ""

# Upstream neighbourhood
echo "### Upstream (depth $DEPTH)"
echo ""

# BFS upstream traversal
jq -r --arg id "$UNIQUE_ID" --argjson depth "$DEPTH" '
  def upstream($uid; $d):
    if $d <= 0 then []
    else
      ((.nodes[$uid] // .sources[$uid] // {}).depends_on.nodes // []) as $deps
      | $deps + ([ $deps[] | upstream(.; $d - 1) ] | flatten)
    end;

  upstream($id; $depth) | unique[] as $dep |
  ((.nodes[$dep] // .sources[$dep] // {}) | {
    unique_id: $dep,
    name: (.name // "unknown"),
    resource_type: (.resource_type // "unknown"),
    relation_name: (.relation_name // "-"),
    materialized: (.config.materialized // "-")
  })
' "$MANIFEST" | jq -s '.' 2>/dev/null || echo "[]"
echo ""

# Downstream neighbourhood (reverse lookup)
echo "### Downstream (depth 1)"
echo ""
jq -r --arg id "$UNIQUE_ID" '
  .nodes | to_entries[]
  | select(.value.resource_type == "model")
  | select((.value.depends_on.nodes // []) | index($id))
  | {
      unique_id: .key,
      name: .value.name,
      resource_type: .value.resource_type,
      relation_name: (.value.relation_name // "-"),
      materialized: (.value.config.materialized // "-")
    }
' "$MANIFEST" | jq -s '.' 2>/dev/null || echo "[]"
echo ""

# Referenced macros
echo "### Referenced macros"
echo ""
jq -r --arg id "$UNIQUE_ID" '
  (.nodes[$id].depends_on.macros // [])[] as $mac |
  (.macros[$mac] // {unique_id: $mac, macro_sql: "<<not in slice>>"})
' "$MANIFEST" | jq -s '.' 2>/dev/null || echo "[]"
