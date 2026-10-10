"""
Comparative Evaluation Module (Phase 6).
Benchmarks MetaOracle (Metamorphic Testing) against:
1. Random Testing (Crash-Only Oracle)
2. Conventional Expected-Output Testing (Handcrafted Unit Tests)
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple
from ..engine.runner import MetamorphicTestRunner
from ..relations.registry import default_registry
from ..sample_programs.sorting import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
    sort_list_buggy_partial,
)
from ..sample_programs.shortest_route import (
    shortest_route,
    shortest_route_buggy_asymmetric,
    shortest_route_buggy_weight,
)
from ..sample_programs.duplicate_removal import (
    remove_duplicates,
    remove_duplicates_buggy_consecutive,
    remove_duplicates_buggy_idempotence,
)


@dataclass
class TechniqueResult:
    """Performance results for a specific testing approach."""
    technique_name: str
    oracle_type: str
    oracle_effort: str
    tests_executed: int
    duration_ms: float
    detected_bugs_count: int
    total_evaluated_bugs: int
    detection_rate: float
    detected_bug_names: List[str] = field(default_factory=list)
    missed_bug_names: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technique_name": self.technique_name,
            "oracle_type": self.oracle_type,
            "oracle_effort": self.oracle_effort,
            "tests_executed": self.tests_executed,
            "duration_ms": round(self.duration_ms, 2),
            "detected_bugs_count": self.detected_bugs_count,
            "total_evaluated_bugs": self.total_evaluated_bugs,
            "detection_rate": round(self.detection_rate, 2),
            "detected_bug_names": self.detected_bug_names,
            "missed_bug_names": self.missed_bug_names,
            "notes": self.notes,
        }


class BenchmarkComparator:
    """Runs a head-to-head empirical comparison across the three testing paradigms."""

    def __init__(self, test_budget: int = 50, seed: int = 42):
        self.test_budget = test_budget
        self.seed = seed
        self.runner = MetamorphicTestRunner(seed=seed)

    def run_full_comparison(self) -> List[TechniqueResult]:
        """Runs the three testing methods on all seeded buggy functions."""
        buggy_variants = [
            ("Sorting (Reverse Bias Bug)", sort_list_buggy_reverse, "sort"),
            ("Sorting (Duplicates Dropped)", sort_list_buggy_duplicates, "sort"),
            ("Sorting (Partial Sort Bug)", sort_list_buggy_partial, "sort"),
            ("Graph (Asymmetric Traversal)", shortest_route_buggy_asymmetric, "graph"),
            ("Graph (Hop Count / Weight Bug)", shortest_route_buggy_weight, "graph"),
            ("Deduplication (Consecutive Only)", remove_duplicates_buggy_consecutive, "dedup"),
            ("Deduplication (Idempotence Failure)", remove_duplicates_buggy_idempotence, "dedup"),
        ]

        # 1. Random Testing (Crash-Only Oracle)
        res_random = self._evaluate_random_testing(buggy_variants)

        # 2. Expected-Output Unit Testing (Manual Oracle)
        res_expected = self._evaluate_expected_output_testing(buggy_variants)

        # 3. MetaOracle (Metamorphic Relations)
        res_meta = self._evaluate_metaoracle_testing(buggy_variants)

        return [res_random, res_expected, res_meta]

    def _evaluate_random_testing(self, bug_suite: List[Tuple[str, Callable, str]]) -> TechniqueResult:
        """
        Random Testing without output oracle:
        Executes random inputs and only flags a bug if the program crashes/raises an exception.
        """
        start = time.perf_counter()
        detected = []
        missed = []
        total_tests = 0

        list_inputs = self.runner.generator.generate_list_inputs(count=self.test_budget)
        graph_inputs = self.runner.generator.generate_graph_inputs(count=self.test_budget)

        for name, fn, f_type in bug_suite:
            inputs = graph_inputs if f_type == "graph" else list_inputs
            crashed = False
            for inp in inputs:
                total_tests += 1
                res = self.runner.executor.execute(fn, inp)
                if not res.success:
                    crashed = True
                    break

            if crashed:
                detected.append(name)
            else:
                missed.append(name)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return TechniqueResult(
            technique_name="Random Testing (Crash Oracle)",
            oracle_type="Crash-Only (Exceptions/Hangs)",
            oracle_effort="Zero manual oracle effort",
            tests_executed=total_tests,
            duration_ms=elapsed_ms,
            detected_bugs_count=len(detected),
            total_evaluated_bugs=len(bug_suite),
            detection_rate=(len(detected) / len(bug_suite)) * 100.0,
            detected_bug_names=detected,
            missed_bug_names=missed,
            notes="Fails to detect silent semantic logic errors where code returns incorrect results without crashing.",
        )

    def _evaluate_expected_output_testing(self, bug_suite: List[Tuple[str, Callable, str]]) -> TechniqueResult:
        """
        Conventional Unit Testing with handcrafted expected outputs.
        Simulates typical developer unit test suites (5-6 fixed manual assertions).
        """
        start = time.perf_counter()
        detected = []
        missed = []
        total_tests = 0

        # Typical developer unit tests (handcrafted inputs with expected outputs)
        manual_sort_tests = [
            ([], []),
            ([1], [1]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 1, 3], [1, 2, 3]),
            ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ]

        manual_dedup_tests = [
            ([], []),
            ([1], [1]),
            ([1, 1], [1]),
            ([1, 2, 2, 3], [1, 2, 3]),
        ]

        triangle_g = {
            "A": {"B": 1.0, "C": 4.0},
            "B": {"A": 1.0, "C": 2.0},
            "C": {"A": 4.0, "B": 2.0},
        }
        manual_graph_tests = [
            ((triangle_g, "A", "A"), 0.0),
            ((triangle_g, "A", "B"), 1.0),
            ((triangle_g, "A", "C"), 3.0),
        ]

        for name, fn, f_type in bug_suite:
            failed = False
            if f_type == "sort":
                for inp, exp in manual_sort_tests:
                    total_tests += 1
                    try:
                        out = fn(list(inp))
                        if out != exp:
                            failed = True
                            break
                    except Exception:
                        failed = True
                        break
            elif f_type == "dedup":
                for inp, exp in manual_dedup_tests:
                    total_tests += 1
                    try:
                        out = fn(list(inp))
                        if out != exp:
                            failed = True
                            break
                    except Exception:
                        failed = True
                        break
            elif f_type == "graph":
                for inp, exp in manual_graph_tests:
                    total_tests += 1
                    try:
                        out = fn(*inp)
                        if out != exp:
                            failed = True
                            break
                    except Exception:
                        failed = True
                        break

            if failed:
                detected.append(name)
            else:
                missed.append(name)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return TechniqueResult(
            technique_name="Expected-Output Unit Testing",
            oracle_type="Manual Handcrafted Oracles",
            oracle_effort="High (Manual calculation & assertion per input)",
            tests_executed=total_tests,
            duration_ms=elapsed_ms,
            detected_bugs_count=len(detected),
            total_evaluated_bugs=len(bug_suite),
            detection_rate=(len(detected) / len(bug_suite)) * 100.0,
            detected_bug_names=detected,
            missed_bug_names=missed,
            notes="Only catches bugs covered by the few manually anticipated test cases. Misses edge cases like non-consecutive duplicates.",
        )

    def _evaluate_metaoracle_testing(self, bug_suite: List[Tuple[str, Callable, str]]) -> TechniqueResult:
        """
        MetaOracle Metamorphic Testing:
        Uses automated relations and automatically generated inputs without manual expected outputs.
        """
        start = time.perf_counter()
        detected = []
        missed = []
        total_tests = 0

        # Map function types to appropriate metamorphic relations
        sort_relations = [
            default_registry.get("MR_REVERSE_INVARIANCE"),
            default_registry.get("MR_PERMUTATION_INVARIANCE"),
            default_registry.get("MR_IDEMPOTENCE"),
            default_registry.get("MR_SCALING_PROPORTIONALITY"),
            default_registry.get("MR_SIZE_CONSERVATION"),
        ]
        graph_relations = [
            default_registry.get("MR_GRAPH_SYMMETRY"),
        ]
        dedup_relations = [
            default_registry.get("MR_IDEMPOTENCE"),
            default_registry.get("MR_DUPLICATE_AMPLIFICATION"),
            default_registry.get("MR_UNIQUE_COMPLETENESS"),
        ]

        list_inputs = self.runner.generator.generate_list_inputs(count=self.test_budget)
        graph_inputs = self.runner.generator.generate_graph_inputs(count=self.test_budget)

        for name, fn, f_type in bug_suite:
            if f_type == "sort":
                rels = sort_relations
                inps = list_inputs
            elif f_type == "graph":
                rels = graph_relations
                inps = graph_inputs
            else:
                rels = dedup_relations
                inps = list_inputs

            rep = self.runner.run_tests(
                target_func=fn,
                relations=[r for r in rels if r is not None],
                inputs=inps,
                function_name=name,
                input_type="graph" if f_type == "graph" else "list",
            )
            total_tests += rep.total_tests

            if rep.has_violations or rep.error_tests > 0:
                detected.append(name)
            else:
                missed.append(name)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return TechniqueResult(
            technique_name="MetaOracle (Metamorphic Testing)",
            oracle_type="Oracle-Free Metamorphic Relations",
            oracle_effort="Low (Relations defined once, inputs generated automatically)",
            tests_executed=total_tests,
            duration_ms=elapsed_ms,
            detected_bugs_count=len(detected),
            total_evaluated_bugs=len(bug_suite),
            detection_rate=(len(detected) / len(bug_suite)) * 100.0,
            detected_bug_names=detected,
            missed_bug_names=missed,
            notes="Detects complex semantic bugs and relation violations without requiring known expected outputs.",
        )
