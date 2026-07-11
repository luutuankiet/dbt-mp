import argparse
import json
import os
import shutil
import subprocess
import sys
import logging
from dbt_mp.models import SlimNode, SlimNodeConfig, SlimSource, SlimMacro, SlimColumn
from dbt_mp.selection import resolve_selection


def resolve_dbt_executable():
    """Locate the dbt CLI to invoke.

    Prefers a project virtualenv in the current working directory (./.venv or
    ./venv) so `uvx dbt-mp` works even when the user hasn't `source`-d their
    project venv, then a currently-active VIRTUAL_ENV, then dbt on PATH.
    """
    candidates = []
    for venv_dir in ('.venv', 'venv'):
        base = os.path.join(os.getcwd(), venv_dir)
        candidates.append(os.path.join(base, 'bin', 'dbt'))
        candidates.append(os.path.join(base, 'Scripts', 'dbt.exe'))  # Windows

    virtual_env = os.environ.get('VIRTUAL_ENV')
    if virtual_env:
        candidates.append(os.path.join(virtual_env, 'bin', 'dbt'))
        candidates.append(os.path.join(virtual_env, 'Scripts', 'dbt.exe'))

    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return shutil.which('dbt') or 'dbt'


def _source_manifest_provenance(manifest):
    """Surface the provenance of the manifest we parsed.

    dbt-mp is intentionally NOT pinned to a manifest schema version - it reads a
    small set of stable, high-signal keys defensively (via .get()), so a newer or
    older manifest degrades gracefully instead of breaking. Echoing the source
    manifest's version here makes any mismatch visible to the consuming agent
    (e.g. "this slice came from dbt 1.11 / manifest v12 in prod") rather than
    silent.
    """
    meta = manifest.get('metadata', {}) or {}
    provenance = {
        'note': (
            'Provenance of the manifest this slice was parsed from. dbt-mp is not '
            'locked to a schema version; it reads stable keys defensively.'
        ),
        'dbt_schema_version': meta.get('dbt_schema_version'),
        'dbt_version': meta.get('dbt_version'),
        'adapter_type': meta.get('adapter_type'),
        'project_name': meta.get('project_name'),
        'generated_at': meta.get('generated_at'),
    }
    # Drop any keys the source manifest didn't provide.
    return {k: v for k, v in provenance.items() if v is not None}


def slim_columns(raw_columns):
    """Slim a manifest 'columns' dict down to name/description/data_type.

    Empty strings are normalised to None (so exclude_none drops them), keeping
    sparsely-documented columns lean. Returns None when there are no columns,
    so the key is omitted entirely from the output.
    """
    if not raw_columns:
        return None

    slimmed = {}
    for col_name, col in raw_columns.items():
        col = col or {}
        slim_col = SlimColumn(
            name=col.get('name') or None,
            description=(col.get('description') or None),
            data_type=(col.get('data_type') or None),
        ).model_dump(exclude_none=True)
        if slim_col:
            slimmed[col_name] = slim_col

    return slimmed or None

def run_dbt_ls(select_statement: str = '', dbt_executable: str = 'dbt'):
    """
    Runs the 'dbt ls' command with the given selection statement
    and returns a list of JSON objects, one for each resource.
    """
    # Corrected command: removed 'macro' from resource types
    try:
        command = [
            dbt_executable,
            "ls",
            "--resource-type", 
            "model", 
            "source", 
            "--output", 
            "json"
            ] 
        command = command + ["--select", select_statement] if select_statement else command
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        # dbt ls writes informative messages to stderr (like "Using default selector...")
        # We should print these to stderr so the user sees them.
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        # The output is a series of JSON objects, one per line.
        return [line for line in result.stdout.strip().split('\n') if line]
    except FileNotFoundError:
        print(
            f"Error: dbt executable '{dbt_executable}' not found. Make sure dbt is installed "
            "(e.g. in your project's ./.venv) and in your PATH, or use --offline to parse an "
            "existing manifest without dbt.",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing dbt command: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def slim_node(node):
    """
    Returns a slimmed-down version of a manifest node dictionary,
    using Pydantic models for validation and schema definition.
    """
    config = node.get('config', {})
    
    # Create config object
    slim_config = SlimNodeConfig(
        materialized=config.get('materialized'),
        enabled=config.get('enabled'),
        incremental_strategy=config.get('incremental_strategy')
    )
    
    # Create node object
    # Note: 'schema' in manifest maps to 'schema_name' in model (aliased as 'schema')
    slim_node_obj = SlimNode(
        schema_name=node.get('schema'),
        name=node.get('name'),
        resource_type=node.get('resource_type'),
        unique_id=node.get('unique_id'),
        relation_name=node.get('relation_name'),
        config=slim_config,
        tags=node.get('tags'),
        columns=slim_columns(node.get('columns')),
        raw_code=node.get('raw_code'),
        refs=node.get('refs'),
        sources=node.get('sources'),
        depends_on=node.get('depends_on'),
        compiled_code=node.get('compiled_code')
    )
    
    return slim_node_obj.model_dump(exclude_none=True, by_alias=True)
    
def slim_source(source):
    """
    Returns a slimmed-down version of a manifest source dictionary.
    """
    slim_source_obj = SlimSource(
        database=source.get('database'),
        schema_name=source.get('schema'),
        name=source.get('name'),
        unique_id=source.get('unique_id'),
        relation_name=source.get('relation_name'),
        description=source.get('description'),
        columns=slim_columns(source.get('columns'))
    )
    return slim_source_obj.model_dump(exclude_none=True, by_alias=True)

def slim_macro(macro):
    """
    Returns a slimmed-down version of a manifest macro dictionary.
    """
    slim_macro_obj = SlimMacro(
        unique_id=macro.get('unique_id'),
        macro_sql=macro.get('macro_sql')
    )
    return slim_macro_obj.model_dump(exclude_none=True, by_alias=True)


def main():
    """
    Main entry point for the dbt-mp CLI tool.
    """
    parser = argparse.ArgumentParser(
        description="A CLI tool to parse and filter dbt manifest.json files."
    )

    parser.add_argument(
        "--select",
        required=False,
        help="The dbt selection syntax to filter the manifest. (e.g., '+stg_orders')",
    )

    parser.add_argument(
        "--manifest-path",
        default="target/manifest.json",
        help="The path to the manifest.json file. Defaults to 'target/manifest.json'."
    )
    
    parser.add_argument(
        "--out-file",
        help="The path to write the filtered manifest JSON file.",
        default='manifest_slim.json'
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Parse an existing (e.g. downloaded prod) manifest without running "
            "'dbt compile'/'dbt ls'. Selection is resolved from the manifest's "
            "parent_map/child_map graph. Everything (compiled_code, relation_name, "
            "deps) is already baked into the manifest, so no dbt project is needed."
        ),
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate that all selected resources are present in the output. Exits 1 if missing items.",
    )

    args = parser.parse_args()

    # Resolve the dbt CLI once (auto-detects a project ./.venv for uvx runs).
    dbt_executable = resolve_dbt_executable()

    # Compile (unless offline) and load the full manifest.json
    try:
        if not args.offline:
            print(f"Using dbt executable: {dbt_executable}")
            compile_command = [dbt_executable, "compile", "--select", args.select] if args.select else [dbt_executable, "compile"]
            print("Compiling models sql with command: " + ' '.join(compile_command))
            subprocess.run(
                compile_command,
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            print(f"Offline mode: using existing manifest at '{args.manifest_path}' (skipping dbt compile/ls).")

        with open(args.manifest_path, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at '{args.manifest_path}'", file=sys.stderr)
        print("Please run 'dbt compile' or another dbt command to generate it.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.manifest_path}'.", file=sys.stderr)
        sys.exit(1)

    if args.offline:
        # Resolve selection directly from the manifest graph - no dbt invocation.
        selected_unique_ids = sorted(resolve_selection(manifest, args.select))
        print(f"Found {len(selected_unique_ids)} matching models and sources from the manifest graph.")
    else:
        # Run 'dbt ls' to get the list of selected models and sources
        ls_output_lines = run_dbt_ls(args.select, dbt_executable)

        selected_unique_ids = []
        for line in ls_output_lines:
            if line.startswith('{'):
                try:
                    json_line = json.loads(line)
                    selected_unique_ids.append(json_line.get('unique_id'))
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from dbt ls output line: {line}", file=sys.stderr)
            else:
                print(line)

        selected_unique_ids = [uid for uid in selected_unique_ids if uid]
        print(f"Found {len(selected_unique_ids)} matching models and sources from 'dbt ls'.")


    # Find all dependent macros
    dependent_macros = set()
    for unique_id in selected_unique_ids:
        node = manifest['nodes'].get(unique_id)
        if node:
            # Add macros from the 'depends_on' dictionary
            macros_in_node = node.get('depends_on', {}).get('macros', [])
            for macro_id in macros_in_node:
                dependent_macros.add(macro_id)

    print(f"Found {len(dependent_macros)} dependent macros.")
    
    # Combine the selected nodes with their dependent macros
    final_selection_set = set(selected_unique_ids) | dependent_macros

    # Filter the manifest and slim it down
    slim_manifest = {
        '$manifest_schema': {
            'description': 'Schema + query guide for the dbt-mp manifest_slim output. Consult before querying.',
            'structure': (
                'Top level: `nodes`, `sources`, `macros` are objects keyed by unique_id. '
                '`$dbt_ls_selection` holds the unique_ids that were explicitly selected; any other '
                'entry in `nodes`/`sources` is an upstream dependency pulled in for context.'
            ),
            'querying_the_warehouse': (
                'To query a model or source in the data warehouse, use its `relation_name` '
                '(already fully-qualified & quoted, e.g. "db"."schema"."table") verbatim in the FROM '
                'clause. Do NOT rebuild it from `schema`+`name` - `relation_name` already accounts for '
                'custom schema/database/alias config.'
            ),
            'jq_recipes': [
                {
                    'question': 'Direct upstream deps (models + sources) of a model',
                    'jq': '.nodes["<unique_id>"].depends_on.nodes'
                },
                {
                    'question': 'Direct deps resolved to their warehouse relation_name',
                    'jq': '.nodes["<unique_id>"].depends_on.nodes[] as $d | (.nodes[$d] // .sources[$d]).relation_name'
                },
                {
                    'question': 'Macros a model depends on',
                    'jq': '.nodes["<unique_id>"].depends_on.macros'
                },
                {
                    'question': 'Reverse lineage: which models depend directly on a given unique_id',
                    'jq': '.nodes | to_entries | map(select(.value.depends_on.nodes // [] | index("<unique_id>"))) | map(.key)'
                },
                {
                    'question': 'Full dependency map: every model -> its direct upstream nodes',
                    'jq': '.nodes | map_values(.depends_on.nodes)'
                },
                {
                    'question': 'Lookup table of every node/source unique_id -> warehouse relation_name',
                    'jq': '(.nodes + .sources) | map_values(.relation_name)'
                }
            ],
            'node_schema': SlimNode.model_json_schema(),
            'source_schema': SlimSource.model_json_schema(),
            'macro_schema': SlimMacro.model_json_schema()
        },
        '$source_manifest': _source_manifest_provenance(manifest),
        '$dbt_ls_selection': selected_unique_ids,
        'selection_used': args.select,
        'nodes': {},
        'sources': {},
        'macros': {}
    }

    # Filter and slim nodes
    for unique_id, node in manifest.get('nodes', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['nodes'][unique_id] = slim_node(node)
            
    # Filter and slim sources
    for unique_id, source in manifest.get('sources', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['sources'][unique_id] = slim_source(source)

    # Filter and slim macros
    for unique_id, macro in manifest.get('macros', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['macros'][unique_id] = slim_macro(macro)

    # 5. Write the result to the output file
    try:
        with open(args.out_file, 'w') as f:
            json.dump(slim_manifest, f, indent=2)
        print(f"Successfully wrote slimmed manifest to '{args.out_file}'")
    except IOError as e:
        print(f"Error writing to file '{args.out_file}': {e}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        expected = set(selected_unique_ids)
        # Note: We check nodes and sources. Macros are often implicit dependencies so strict validation
        # on dbt ls output (which might not list macros unless selected) vs manifest (which has them in depends_on)
        # can be tricky. We focus on the primary selected resources.
        actual = set(slim_manifest['nodes'].keys()) | set(slim_manifest['sources'].keys())
        missing = expected - actual
        
        if missing:
            print(f"VALIDATION FAILED - Missing {len(missing)} items:", file=sys.stderr)
            for item in sorted(missing):
                print(f"  - {item}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"VALIDATION PASSED - All {len(expected)} items present")
            sys.exit(0)


if __name__ == "__main__":
    main()