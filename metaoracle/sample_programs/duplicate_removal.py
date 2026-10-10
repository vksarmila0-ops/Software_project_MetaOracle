"""
Duplicate removal algorithms: Reference implementation and seeded bug variants.
Demonstrates Idempotence: f(f(x)) == f(x), and element preservation.
"""

from typing import List, Any


def remove_duplicates(items: List[Any]) -> List[Any]:
    """
    Removes duplicate elements while preserving original insertion order.
    Correct reference implementation.
    Satisfies idempotence: remove_duplicates(remove_duplicates(items)) == remove_duplicates(items).
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def remove_duplicates_buggy_consecutive(items: List[Any]) -> List[Any]:
    """
    BUG VARIANT 1:
    Only removes *consecutive* duplicates (analogous to Unix `uniq`).
    Leaves non-consecutive duplicates intact.
    For example: [1, 2, 1] -> [1, 2, 1].
    Violates set preservation / duplicate completeness.
    """
    if not items:
        return []
    result = [items[0]]
    for i in range(1, len(items)):
        if items[i] != items[i - 1]:
            result.append(items[i])
    return result


def remove_duplicates_buggy_idempotence(items: List[Any]) -> List[Any]:
    """
    BUG VARIANT 2:
    Only removes the FIRST duplicate instance per pass rather than all duplicates.
    Example:
      Input: [1, 1, 1]
      Pass 1: [1, 1]
      Pass 2: [1]
    Directly violates Idempotence: f(f(x)) != f(x).
    """
    if not items:
        return []
    seen = set()
    result = []
    removed_one = False

    for item in items:
        if item in seen and not removed_one:
            # Drop only the first duplicate encountered in this run
            removed_one = True
            continue
        seen.add(item)
        result.append(item)
    return result
