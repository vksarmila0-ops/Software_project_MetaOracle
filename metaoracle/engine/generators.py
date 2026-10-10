"""
Input generators for metamorphic testing in MetaOracle.
Supports both Hypothesis strategies and built-in synthetic generation with boundary testing.
"""

import random
from typing import Any, Dict, List, Tuple

try:
    from hypothesis import strategies as st
    from hypothesis.strategies import SearchStrategy
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False


class InputGenerator:
    """Configurable input generator producing realistic, diverse, and edge-case inputs."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_list_inputs(
        self,
        count: int = 50,
        min_len: int = 0,
        max_len: int = 20,
        allow_negatives: bool = True,
    ) -> List[List[int]]:
        """
        Generates list inputs including deterministic edge cases and random variations.
        """
        inputs: List[List[int]] = []

        # 1. Edge and Boundary Cases
        edge_cases = [
            [],
            [0],
            [1],
            [-1],
            [42, 42],
            [1, 2, 3, 4, 5],
            [5, 4, 3, 2, 1],
            [1, 1, 1, 1],
            [-10, 0, 10],
            [3, -1, 4, -1, 5, 9, 2, 6, 5],
            [100, -100, 50, -50, 0],
            [2, 1],
            [1, 2],
        ]
        for ec in edge_cases:
            if len(inputs) < count:
                inputs.append(list(ec))

        # 2. Random Generative Inputs
        min_val = -100 if allow_negatives else 0
        max_val = 100

        while len(inputs) < count:
            length = self.rng.randint(max(1, min_len), max_len)
            # 50% chance of duplicates, 20% strictly descending, 30% arbitrary
            mode = self.rng.random()
            if mode < 0.2:
                # Descending sequence
                seq = sorted([self.rng.randint(min_val, max_val) for _ in range(length)], reverse=True)
            elif mode < 0.5:
                # High duplicate density
                vocab = [self.rng.randint(min_val, max_val) for _ in range(max(2, length // 3))]
                seq = [self.rng.choice(vocab) for _ in range(length)]
            else:
                # Arbitrary uniform integers
                seq = [self.rng.randint(min_val, max_val) for _ in range(length)]

            inputs.append(seq)

        return inputs[:count]

    def generate_graph_inputs(
        self,
        count: int = 30,
        min_nodes: int = 3,
        max_nodes: int = 7,
    ) -> List[Tuple[Dict[str, Dict[str, float]], str, str]]:
        """
        Generates undirected weighted graph inputs: (graph, start_node, end_node).
        Weights are strictly symmetric: graph[u][v] == graph[v][u].
        """
        inputs: List[Tuple[Dict[str, Dict[str, float]], str, str]] = []
        node_letters = ["A", "B", "C", "D", "E", "F", "G", "H"]

        # Deterministic boundary graphs
        triangle_graph = {
            "A": {"B": 1.0, "C": 4.0},
            "B": {"A": 1.0, "C": 2.0},
            "C": {"A": 4.0, "B": 2.0},
        }
        inputs.append((triangle_graph, "A", "C"))
        inputs.append((triangle_graph, "A", "A"))  # Start == End

        linear_graph = {
            "A": {"B": 2.5},
            "B": {"A": 2.5, "C": 3.0},
            "C": {"B": 3.0},
        }
        inputs.append((linear_graph, "A", "C"))

        while len(inputs) < count:
            num_nodes = self.rng.randint(min_nodes, max_nodes)
            nodes = node_letters[:num_nodes]
            graph: Dict[str, Dict[str, float]] = {node: {} for node in nodes}

            # Generate spanning tree to ensure basic connectivity
            shuffled_nodes = list(nodes)
            self.rng.shuffle(shuffled_nodes)
            for i in range(1, len(shuffled_nodes)):
                u = shuffled_nodes[i]
                v = self.rng.choice(shuffled_nodes[:i])
                weight = round(self.rng.uniform(1.0, 15.0), 1)
                graph[u][v] = weight
                graph[v][u] = weight

            # Add random additional edges
            for _ in range(self.rng.randint(1, num_nodes * 2)):
                u, v = self.rng.sample(nodes, 2)
                if v not in graph[u]:
                    weight = round(self.rng.uniform(1.0, 15.0), 1)
                    graph[u][v] = weight
                    graph[v][u] = weight

            # Select start and end nodes
            start_node = self.rng.choice(nodes)
            end_node = self.rng.choice(nodes)
            inputs.append((graph, start_node, end_node))

        return inputs[:count]

    def get_hypothesis_strategy_for_lists():
        """Returns a Hypothesis search strategy for lists of integers."""
        if not HYPOTHESIS_AVAILABLE:
            return None
        return st.lists(st.integers(min_value=-1000, max_value=1000), max_size=30)
