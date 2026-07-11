"""Offline dbt node selection.

Resolves a (subset of) dbt's graph selection syntax directly against a
manifest's ``parent_map``/``child_map``, so a downloaded prod ``manifest.json``
can be sliced without invoking ``dbt ls``/``dbt compile``.

Supported syntax (union on whitespace, like dbt):
    model_name          the node itself
    +model_name         node + all ancestors (upstream)
    model_name+         node + all descendants (downstream)
    +model_name+        node + all ancestors and descendants
    N+model_name        ancestors up to N edges
    model_name+N        descendants up to N edges

A selector matches a resource when its value equals the resource's
``unique_id``, its ``name``, or appears in its ``fqn``. Method selectors
(``tag:``, ``path:``, ``config.``, set operators, etc.) are not supported
offline - use the live dbt path for those.
"""
import re

_LEAD = re.compile(r'^(\d*)\+')
_TRAIL = re.compile(r'\+(\d*)$')


def _parse_operators(token):
    """Strip graph operators from a token.

    Returns (up, down, name) where up/down are 0 (none), -1 (unlimited) or a
    positive edge count.
    """
    up = down = 0
    lead = _LEAD.match(token)
    if lead:
        up = int(lead.group(1)) if lead.group(1) else -1
        token = token[lead.end():]
    trail = _TRAIL.search(token)
    if trail:
        down = int(trail.group(1)) if trail.group(1) else -1
        token = token[:trail.start()]
    return up, down, token


def _matches(unique_id, resource, value):
    if unique_id == value:
        return True
    if resource.get('name') == value:
        return True
    if value in (resource.get('fqn') or []):
        return True
    return False


def _walk(start, graph, degree):
    """Breadth-first walk from ``start`` over ``graph`` up to ``degree`` edges.

    ``degree`` of -1 means unlimited. The start node is not included.
    """
    result = set()
    if degree == 0:
        return result
    frontier = {start}
    seen = {start}
    steps = 0
    while frontier:
        if degree != -1 and steps >= degree:
            break
        nxt = set()
        for uid in frontier:
            for adj in graph.get(uid, []):
                if adj not in seen:
                    seen.add(adj)
                    result.add(adj)
                    nxt.add(adj)
        frontier = nxt
        steps += 1
    return result


def resolve_selection(manifest, select_str):
    """Resolve a dbt-style selection string against a manifest.

    Returns a set of unique_ids (models + sources). An empty/None selector
    selects every node and source in the manifest.
    """
    resources = {}
    resources.update(manifest.get('nodes', {}))
    resources.update(manifest.get('sources', {}))

    if not select_str or not select_str.strip():
        return set(resources.keys())

    parent_map = manifest.get('parent_map', {})
    child_map = manifest.get('child_map', {})

    selected = set()
    for token in select_str.split():
        up, down, name = _parse_operators(token)
        roots = {uid for uid, res in resources.items() if _matches(uid, res, name)}
        if not roots:
            print(f"Warning: selector '{token}' matched no resources in the manifest.")
        for root in roots:
            selected.add(root)
            if up != 0:
                selected |= _walk(root, parent_map, up)
            if down != 0:
                selected |= _walk(root, child_map, down)

    # Keep only ids that are actually nodes or sources (graph maps can reference
    # tests/exposures we don't slim).
    return selected & set(resources.keys())
