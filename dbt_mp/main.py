import argparse
import json
import subprocess
import sys
import logging
from dbt_mp.models import SlimNode, SlimNodeConfig, SlimSource, SlimMacro
from dbt_mp.selection import resolve_selection

def run_dbt_ls(select_statement: str = ''):
    """
    Runs the 'dbt ls' command with the given selection statement
    and returns a list of JSON objects, one for each resource.
    """
    # Corrected command: removed 'macro' from resource types
    try:
        command = [
            "dbt", 
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
        print("Error: 'dbt' command not found. Make sure dbt is installed and in your PATH.", file=sys.stderr)
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
        description=source.get('description')
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

    # Compile (unless offline) and load the full manifest.json
    try:
        if not args.offline:
            compile_command = ["dbt", "compile", "--select", args.select] if args.select else ["dbt", "compile"]
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
        ls_output_lines = run_dbt_ls(args.select)

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