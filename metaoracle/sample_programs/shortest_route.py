"""
Graph Shortest Route algorithms: Reference implementation and seeded bug variants.
Uses Dijkstra's algorithm for undirected graphs with non-negative edge weights.
"""

import heapq
from typing import Dict, Any, Optional

GraphType = Dict[str, Dict[str, float]]


def shortest_route(graph: GraphType, start: str, end: str) -> float:
    """
    Computes shortest distance between start and end in an undirected weighted graph.
    Returns float distance or float('inf') if no path exists.
    Correct reference implementation.
    """
    if start == end:
        return 0.0
    if start not in graph or end not in graph:
        return float("inf")

    distances: Dict[str, float] = {node: float("inf") for node in graph}
    distances[start] = 0.0
    pq = [(0.0, start)]
    visited = set()

    while pq:
        curr_dist, curr_node = heapq.heappop(pq)
        if curr_node in visited:
            continue
        visited.add(curr_node)

        if curr_node == end:
            return curr_dist

        for neighbor, weight in graph.get(curr_node, {}).items():
            if weight < 0:
                continue  # Dijkstra requires non-negative weights
            new_dist = curr_dist + weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))

    return distances.get(end, float("inf"))


def shortest_route_buggy_asymmetric(graph: GraphType, start: str, end: str) -> float:
    """
    BUG VARIANT 1:
    Asymmetric traversal bug: The developer introduced directional edge filtering
    or priority bias where edges are only traversed if neighbor >= curr_node
    alphabetically, or applies an extra hop penalty only in forward direction.
    Violates undirected symmetry: route(graph, A, B) != route(graph, B, A).
    """
    if start == end:
        return 0.0
    if start not in graph or end not in graph:
        return float("inf")

    distances: Dict[str, float] = {node: float("inf") for node in graph}
    distances[start] = 0.0
    pq = [(0.0, start)]
    visited = set()

    while pq:
        curr_dist, curr_node = heapq.heappop(pq)
        if curr_node in visited:
            continue
        visited.add(curr_node)

        if curr_node == end:
            return curr_dist

        for neighbor, weight in graph.get(curr_node, {}).items():
            # BUG: Asymmetric bias - penalizes edge when neighbor comes before current alphabetically
            biased_weight = weight
            if neighbor < curr_node:
                biased_weight += 2.0  # Asymmetric penalty!

            new_dist = curr_dist + biased_weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))

    return distances.get(end, float("inf"))


def shortest_route_buggy_weight(graph: GraphType, start: str, end: str) -> float:
    """
    BUG VARIANT 2:
    Ignores the final edge weight or fails to update distances properly,
    or returns hop count instead of weighted distance.
    """
    if start == end:
        return 0.0
    if start not in graph or end not in graph:
        return float("inf")

    # Bug: ignores edge weights and treats all edge costs as 1.0 (unweighted BFS style)
    queue = [(start, 0.0)]
    visited = {start}

    while queue:
        curr_node, curr_dist = queue.pop(0)
        if curr_node == end:
            return curr_dist

        for neighbor in sorted(graph.get(curr_node, {}).keys()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, curr_dist + 1.0))

    return float("inf")
