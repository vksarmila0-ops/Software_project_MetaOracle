"""
Sorting algorithms: Reference correct implementation and seeded bug variants.
"""

from typing import List


def sort_list(items: List[int]) -> List[int]:
    """
    Sorts a list of integers in ascending order.
    Correct reference implementation.
    """
    arr = list(items)
    # Standard quicksort / timsort equivalent
    return sorted(arr)


def sort_list_buggy_reverse(items: List[int]) -> List[int]:
    """
    BUG VARIANT 1:
    Heuristic bug: If the input list starts in descending order (e.g. items[0] > items[-1]),
    it mistakenly flips the comparison logic and sorts in descending order instead of ascending.
    Violates reverse-input invariance and permutation invariance!
    """
    if len(items) <= 1:
        return list(items)
    
    arr = list(items)
    # Faulty optimization: developer assumed descending input should produce descending output
    if arr[0] > arr[-1]:
        return sorted(arr, reverse=True)
    return sorted(arr)


def sort_list_buggy_duplicates(items: List[int]) -> List[int]:
    """
    BUG VARIANT 2:
    Drops duplicate elements during sorting.
    Developer used set conversion: set(arr).
    Violates length conservation / permutation relations with duplicates.
    """
    # Flawed implementation converting to set first
    return sorted(list(set(items)))


def sort_list_buggy_partial(items: List[int]) -> List[int]:
    """
    BUG VARIANT 3:
    Off-by-one boundary bug: In bubble-sort loop, developer stopped the outer
    loop one step too early: range(len(arr) - 2), leaving the last element unsorted
    if it was out of order.
    """
    arr = list(items)
    n = len(arr)
    if n <= 1:
        return arr
    
    # Off-by-one: skips last element sorting pass
    for i in range(max(0, n - 2)):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
