"""
Registry of supported preset algorithms, bug variants, and sample code.
"""

import inspect
from typing import Callable, Dict, Optional, Tuple
from metaoracle.sample_programs import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
    sort_list_buggy_partial,
    shortest_route,
    shortest_route_buggy_asymmetric,
    shortest_route_buggy_weight,
    remove_duplicates,
    remove_duplicates_buggy_consecutive,
    remove_duplicates_buggy_idempotence,
)

PRESET_VARIANTS: Dict[str, Dict[str, Tuple[Callable, str, str]]] = {
    "Sorting": {
        "Correct Reference": (
            sort_list,
            "list",
            "Reference ascending Timsort/Quicksort implementation satisfying all invariant metamorphic relations.",
        ),
        "Bug: Reverse Input Bias": (
            sort_list_buggy_reverse,
            "list",
            "Inverts sorting to descending when arr[0] > arr[-1], violating Permutation and Reverse Invariance.",
        ),
        "Bug: Drops Duplicates (set conversion)": (
            sort_list_buggy_duplicates,
            "list",
            "Converts list to set() during sorting, dropping duplicates and violating Size Conservation.",
        ),
        "Bug: Off-by-one Boundary Partial Sort": (
            sort_list_buggy_partial,
            "list",
            "Off-by-one loop index fails to sort boundary elements, violating Invariance properties.",
        ),
    },
    "Shortest Path": {
        "Correct Reference": (
            shortest_route,
            "graph",
            "Standard Dijkstra shortest path algorithm on undirected weighted graphs.",
        ),
        "Bug: Asymmetric Directional Bias": (
            shortest_route_buggy_asymmetric,
            "graph",
            "Introduces alphabetical directional tie-breaking bias, violating Graph Undirected Symmetry.",
        ),
        "Bug: Unweighted Hop Count": (
            shortest_route_buggy_weight,
            "graph",
            "Calculates shortest unweighted hop count instead of considering edge weights.",
        ),
    },
    "Duplicate Removal": {
        "Correct Reference": (
            remove_duplicates,
            "list",
            "Order-preserving unique element filter, satisfying Idempotence and Unique Completeness.",
        ),
        "Bug: Consecutive-Only Removal": (
            remove_duplicates_buggy_consecutive,
            "list",
            "Only drops consecutive duplicates (like Unix uniq), violating Non-consecutive Invariance.",
        ),
        "Bug: Idempotence Failure (1 drop per run)": (
            remove_duplicates_buggy_idempotence,
            "list",
            "Drops at most one duplicate occurrence per run, violating Idempotence f(f(x)) == f(x).",
        ),
    },
}

DEFAULT_CUSTOM_CODE = '''def custom_function(items):
    """
    Example custom function for metamorphic testing.
    Change the logic or introduce edge-case bugs to test.
    """
    if not items:
        return []
    # Try sorting items
    return sorted(items)
'''


def get_preset_function(category: str, variant: str) -> Optional[Callable]:
    """Resolves callable for a category and variant name."""
    cat_dict = PRESET_VARIANTS.get(category)
    if cat_dict and variant in cat_dict:
        return cat_dict[variant][0]
    return None


def get_preset_input_type(category: str, variant: str) -> str:
    """Returns the input generator type ('list' or 'graph')."""
    cat_dict = PRESET_VARIANTS.get(category)
    if cat_dict and variant in cat_dict:
        return cat_dict[variant][1]
    return "list"


def get_preset_description(category: str, variant: str) -> str:
    """Returns the description of the algorithm/bug variant."""
    cat_dict = PRESET_VARIANTS.get(category)
    if cat_dict and variant in cat_dict:
        return cat_dict[variant][2]
    return "User custom algorithm"


def get_preset_code(category: str, variant: str) -> str:
    """Returns the source code string for the preset function."""
    fn = get_preset_function(category, variant)
    if fn:
        try:
            return inspect.getsource(fn)
        except Exception:
            pass
    return DEFAULT_CUSTOM_CODE


def list_all_presets():
    """Returns a structured listing of all available preset categories and variants."""
    presets = []
    for cat, variants in PRESET_VARIANTS.items():
        for var_name, (fn, input_type, desc) in variants.items():
            presets.append({
                "category": cat,
                "variant": var_name,
                "function_name": fn.__name__,
                "input_type": input_type,
                "description": desc,
            })
    return presets
