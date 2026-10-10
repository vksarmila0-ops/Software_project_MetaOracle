"""
Tests for MetaOracle Metamorphic Relations Catalog.
"""

import pytest
from metaoracle.relations.registry import default_registry
from metaoracle.relations.catalog import (
    ReverseInputInvarianceRelation,
    PermutationInvarianceRelation,
    IdempotenceRelation,
    GraphSymmetryRelation,
    ScalingProportionalityRelation,
    AdditiveShiftEquivarianceRelation,
    DuplicateAmplificationInvarianceRelation,
    SubsetInclusionMonotonicityRelation,
    SizeConservationRelation,
    UniqueCompletenessRelation,
)


def test_reverse_input_invariance_passes_on_symmetric():
    mr = ReverseInputInvarianceRelation()
    # If source output and follow-up output are equal
    res = mr.check([1, 2, 3], [3, 2, 1], [1, 2, 3], [1, 2, 3])
    assert res.passed is True


def test_reverse_input_invariance_fails_on_asymmetric():
    mr = ReverseInputInvarianceRelation()
    res = mr.check([1, 2, 3], [3, 2, 1], [1, 2, 3], [3, 2, 1])
    assert res.passed is False
    assert "Violation" in res.message


def test_permutation_invariance_transform():
    mr = PermutationInvarianceRelation(seed=42)
    inp = [1, 2, 3, 4, 5, 6, 7]
    transformed = mr.transform(inp)
    assert set(transformed) == set(inp)
    assert len(transformed) == len(inp)


def test_idempotence_check():
    mr = IdempotenceRelation()
    # f(f(x)) == f(x)
    res_pass = mr.check([1, 2, 2], [1, 2], [1, 2], [1, 2])
    assert res_pass.passed is True

    # f(f(x)) != f(x)
    res_fail = mr.check([1, 1, 1], [1, 1], [1, 1], [1])
    assert res_fail.passed is False


def test_graph_symmetry_transform_and_check():
    mr = GraphSymmetryRelation()
    g = {"A": {"B": 2.0}, "B": {"A": 2.0}}
    transformed = mr.transform((g, "A", "B"))
    assert transformed == (g, "B", "A")

    res_pass = mr.check((g, "A", "B"), (g, "B", "A"), 2.0, 2.0)
    assert res_pass.passed is True

    res_fail = mr.check((g, "A", "B"), (g, "B", "A"), 2.0, 4.0)
    assert res_fail.passed is False


def test_scaling_proportionality():
    mr = ScalingProportionalityRelation(factor=2)
    assert mr.transform([1, 2, 3]) == [2, 4, 6]
    res = mr.check([1, 2], [2, 4], [1, 2], [2, 4])
    assert res.passed is True


def test_size_conservation_relation():
    mr = SizeConservationRelation()
    # Passing: len output matches len input
    res_pass = mr.check([1, 2, 3], [1, 2, 3, 1, 2, 3], [1, 2, 3], [1, 2, 3, 1, 2, 3])
    assert res_pass.passed is True

    # Violation: drops duplicates
    res_fail = mr.check([1, 2, 2], [1, 2, 2, 1, 2, 2], [1, 2], [1, 2])
    assert res_fail.passed is False


def test_unique_completeness_relation():
    mr = UniqueCompletenessRelation()
    res_pass = mr.check([1, 2, 2], [1, 2], [1, 2], [1, 2])
    assert res_pass.passed is True

    # Flawed: retains duplicates
    res_fail = mr.check([1, 2, 1], [1, 2, 1], [1, 2, 1], [1, 2, 1])
    assert res_fail.passed is False


def test_default_registry_has_relations():
    all_rels = default_registry.list_all()
    assert len(all_rels) >= 8
    assert default_registry.get("MR_REVERSE_INVARIANCE") is not None
    assert default_registry.get("MR_GRAPH_SYMMETRY") is not None
