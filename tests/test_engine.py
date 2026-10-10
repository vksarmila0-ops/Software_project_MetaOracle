"""
Tests for MetaOracle Testing Engine (SafeExecutor, InputGenerator, MetamorphicTestRunner).
"""

import time
import pytest
from metaoracle.engine.executor import SafeExecutor
from metaoracle.engine.generators import InputGenerator
from metaoracle.engine.runner import MetamorphicTestRunner
from metaoracle.relations.registry import default_registry
from metaoracle.sample_programs.sorting import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
)
from metaoracle.sample_programs.shortest_route import (
    shortest_route,
    shortest_route_buggy_asymmetric,
)
from metaoracle.sample_programs.duplicate_removal import (
    remove_duplicates,
    remove_duplicates_buggy_idempotence,
)


def test_safe_executor_success():
    executor = SafeExecutor(timeout_seconds=2.0)
    res = executor.execute(lambda x: x * 2, 5)
    assert res.success is True
    assert res.output == 10
    assert res.error_type is None


def test_safe_executor_exception_handling():
    def failing_fn(x):
        raise ValueError("Intentional exception")

    executor = SafeExecutor(timeout_seconds=2.0)
    res = executor.execute(failing_fn, 5)
    assert res.success is False
    assert res.error_type == "ValueError"
    assert "Intentional exception" in res.error_message


def test_safe_executor_timeout():
    def infinite_loop(x):
        time.sleep(1.0)
        return x

    executor = SafeExecutor(timeout_seconds=0.2)
    res = executor.execute(infinite_loop, 5)
    assert res.success is False
    assert res.timed_out is True
    assert res.error_type == "TimeoutError"


def test_input_generator_lists():
    gen = InputGenerator(seed=42)
    inputs = gen.generate_list_inputs(count=20)
    assert len(inputs) == 20
    # Boundary cases must be present
    assert [] in inputs
    assert [0] in inputs


def test_input_generator_graphs():
    gen = InputGenerator(seed=42)
    graphs = gen.generate_graph_inputs(count=10)
    assert len(graphs) == 10
    g, start, end = graphs[0]
    assert isinstance(g, dict)
    assert start in g
    # Symmetry property of generated undirected graph
    for u in g:
        for v in g[u]:
            assert g[u][v] == g[v][u]


def test_runner_on_correct_sorting():
    runner = MetamorphicTestRunner(seed=42)
    rels = [
        default_registry.get("MR_REVERSE_INVARIANCE"),
        default_registry.get("MR_PERMUTATION_INVARIANCE"),
        default_registry.get("MR_IDEMPOTENCE"),
    ]
    report = runner.run_tests(sort_list, rels, test_count=20, input_type="list")
    assert report.total_tests == 60
    assert report.violated_tests == 0
    assert report.passed_tests == 60
    assert report.has_violations is False


def test_runner_detects_buggy_reverse():
    runner = MetamorphicTestRunner(seed=42)
    rels = [
        default_registry.get("MR_REVERSE_INVARIANCE"),
        default_registry.get("MR_PERMUTATION_INVARIANCE"),
    ]
    report = runner.run_tests(sort_list_buggy_reverse, rels, test_count=25, input_type="list")
    assert report.violated_tests > 0
    assert report.has_violations is True
    assert len(report.all_counterexamples) > 0


def test_runner_detects_buggy_graph_asymmetric():
    runner = MetamorphicTestRunner(seed=42)
    rel = default_registry.get("MR_GRAPH_SYMMETRY")
    report = runner.run_tests(shortest_route_buggy_asymmetric, [rel], test_count=15, input_type="graph")
    assert report.violated_tests > 0
    assert report.has_violations is True


def test_runner_detects_buggy_dedup_idempotence():
    runner = MetamorphicTestRunner(seed=42)
    rel = default_registry.get("MR_IDEMPOTENCE")
    report = runner.run_tests(remove_duplicates_buggy_idempotence, [rel], test_count=25, input_type="list")
    assert report.violated_tests > 0
    assert report.has_violations is True
