"""
Tests for Relation Suggester, Mutation Testing, and Evaluation modules.
"""

import pytest
from metaoracle.suggestion.suggester import RelationSuggester
from metaoracle.mutation.mutators import MutantGenerator
from metaoracle.mutation.engine import MutationTester
from metaoracle.evaluation.comparator import BenchmarkComparator
from metaoracle.relations.registry import default_registry
from metaoracle.sample_programs.sorting import sort_list


def test_suggester_sort_list():
    suggester = RelationSuggester()
    code = """
def sort_list(items):
    return sorted(items)
"""
    suggestions = suggester.suggest_from_code(code)
    suggested_ids = [s.relation.relation_id for s in suggestions]
    assert "MR_PERMUTATION_INVARIANCE" in suggested_ids
    assert "MR_REVERSE_INVARIANCE" in suggested_ids
    assert "MR_IDEMPOTENCE" in suggested_ids


def test_suggester_graph_route():
    suggester = RelationSuggester()
    code = """
def shortest_route(graph, start, end):
    return 0.0
"""
    suggestions = suggester.suggest_from_code(code)
    suggested_ids = [s.relation.relation_id for s in suggestions]
    assert "MR_GRAPH_SYMMETRY" in suggested_ids


def test_suggester_duplicate_removal():
    suggester = RelationSuggester()
    code = """
def remove_duplicates(items):
    seen = set()
    return list(seen)
"""
    suggestions = suggester.suggest_from_code(code)
    suggested_ids = [s.relation.relation_id for s in suggestions]
    assert "MR_IDEMPOTENCE" in suggested_ids


def test_mutant_generator():
    code = "def check(a, b):\n    if a > b:\n        return a + 1\n    return 0\n"
    gen = MutantGenerator()
    mutants = gen.generate_mutants(code, max_mutants=10)
    assert len(mutants) > 0
    # Check that diff is populated
    assert mutants[0].diff != ""
    assert mutants[0].mutated_code != code


def test_mutation_tester_calculates_score():
    tester = MutationTester(seed=42)
    code = """
def sort_list(items):
    arr = list(items)
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""
    rels = [
        default_registry.get("MR_REVERSE_INVARIANCE"),
        default_registry.get("MR_PERMUTATION_INVARIANCE"),
        default_registry.get("MR_SIZE_CONSERVATION"),
    ]
    report = tester.run_mutation_analysis(code, rels, test_count=15, max_mutants=5)
    assert report.total_mutants > 0
    assert report.mutation_score >= 0.0
    assert report.killed_mutants + report.survived_mutants == report.total_mutants


def test_benchmark_comparator():
    comparator = BenchmarkComparator(test_budget=15, seed=42)
    results = comparator.run_full_comparison()
    assert len(results) == 3
    # Check that MetaOracle achieves higher or equal bug detection compared to Random
    names = [r.technique_name for r in results]
    assert "Random Testing (Crash Oracle)" in names[0]
    assert "Expected-Output Unit Testing" in names[1]
    assert "MetaOracle (Metamorphic Testing)" in names[2]
    assert results[2].detection_rate > results[0].detection_rate
