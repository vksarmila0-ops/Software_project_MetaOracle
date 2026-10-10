"""Sample programs for MetaOracle testing: correct implementations and seeded bug variants."""

from .sorting import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
    sort_list_buggy_partial,
)
from .shortest_route import (
    shortest_route,
    shortest_route_buggy_asymmetric,
    shortest_route_buggy_weight,
)
from .duplicate_removal import (
    remove_duplicates,
    remove_duplicates_buggy_consecutive,
    remove_duplicates_buggy_idempotence,
)

__all__ = [
    "sort_list",
    "sort_list_buggy_reverse",
    "sort_list_buggy_duplicates",
    "sort_list_buggy_partial",
    "shortest_route",
    "shortest_route_buggy_asymmetric",
    "shortest_route_buggy_weight",
    "remove_duplicates",
    "remove_duplicates_buggy_consecutive",
    "remove_duplicates_buggy_idempotence",
]
