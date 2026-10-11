"""
13 Extended Test Cases for MetaOracle Testing Studio & Platform.
Covers:
- Metamorphic Relation invariants (Additive Shift, Duplicate Amplification, Subset Monotonicity)
- Registry category filtering & edge cases
- SafeExecutor immutability, scalar handling, and dynamic code compiling
- InputGenerator boundary & edge cases
- SQLite database cascade deletion and multi-filter history querying
- FastAPI REST API 404 error handling, custom relation lifecycle, and snippet deletion
- Benchmark comparator detailed detection metrics
"""

import copy
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database.session import Base, init_db
from backend.app.database.models import TestRun, TestCase, CustomRelation, CodeSnippet
from backend.app.services.test_service import get_test_history, delete_test_run
from backend.app.services.snippet_service import delete_snippet, get_snippet, create_snippet

from metaoracle.relations.registry import default_registry, RelationRegistry
from metaoracle.relations.catalog import (
    AdditiveShiftEquivarianceRelation,
    DuplicateAmplificationInvarianceRelation,
    SubsetInclusionMonotonicityRelation,
)
from metaoracle.engine.executor import SafeExecutor
from metaoracle.engine.generators import InputGenerator
from metaoracle.sample_programs.sorting import sort_list, sort_list_buggy_reverse
from metaoracle.sample_programs.duplicate_removal import remove_duplicates
from metaoracle.evaluation.comparator import BenchmarkComparator


# ------------------------------------------------------------------------------
# 1. Metamorphic Relations: Additive Shift Equivariance
# ------------------------------------------------------------------------------
def test_case_01_additive_shift_equivariance_relation():
    """Test Case 1: Verifies AdditiveShiftEquivarianceRelation transform and invariant check."""
    mr = AdditiveShiftEquivarianceRelation(shift=5)
    source_input = [10, 20, 30]
    follow_up_input = mr.transform(source_input)
    assert follow_up_input == [15, 25, 35]

    # Passing case: f(x + 5) == f(x) + 5
    res_pass = mr.check(source_input, follow_up_input, [10, 20, 30], [15, 25, 35])
    assert res_pass.passed is True
    assert "Additive shift equivariance holds" in res_pass.message

    # Failing case: offset is incorrect
    res_fail = mr.check(source_input, follow_up_input, [10, 20, 30], [10, 20, 30])
    assert res_fail.passed is False
    assert "Violation" in res_fail.message


# ------------------------------------------------------------------------------
# 2. Metamorphic Relations: Duplicate Amplification Invariance
# ------------------------------------------------------------------------------
def test_case_02_duplicate_amplification_invariance_relation():
    """Test Case 2: Verifies DuplicateAmplificationInvarianceRelation on deduplication."""
    mr = DuplicateAmplificationInvarianceRelation()
    source_input = [1, 2, 3]
    amplified_input = mr.transform(source_input)
    assert amplified_input == [1, 1, 2, 2, 3, 3]

    # Valid deduplication preserves unique output
    res_pass = mr.check(source_input, amplified_input, [1, 2, 3], [1, 2, 3])
    assert res_pass.passed is True

    # Flawed deduplication altered by duplicate count
    res_fail = mr.check(source_input, amplified_input, [1, 2, 3], [1, 1, 2, 2, 3, 3])
    assert res_fail.passed is False
    assert "Violation" in res_fail.message


# ------------------------------------------------------------------------------
# 3. Metamorphic Relations: Subset Inclusion Length Monotonicity
# ------------------------------------------------------------------------------
def test_case_03_subset_inclusion_length_monotonicity_relation():
    """Test Case 3: Verifies SubsetInclusionMonotonicityRelation len(f(x + [y])) >= len(f(x))."""
    mr = SubsetInclusionMonotonicityRelation(item_to_add=99)
    source_input = [1, 2, 3]
    extended_input = mr.transform(source_input)
    assert extended_input == [1, 2, 3, 99]

    # Passing: output length is greater or equal
    res_pass = mr.check(source_input, extended_input, [1, 2, 3], [1, 2, 3, 99])
    assert res_pass.passed is True

    # Failing: output length unexpectedly decreased
    res_fail = mr.check(source_input, extended_input, [1, 2, 3], [1, 2])
    assert res_fail.passed is False
    assert "Violation" in res_fail.message


# ------------------------------------------------------------------------------
# 4. Registry: Category Filtering & Non-existent Relation Queries
# ------------------------------------------------------------------------------
def test_case_04_relation_registry_category_and_retrieval_edge_cases():
    """Test Case 4: Verifies registry category querying and graceful None on unknown ID."""
    reg = RelationRegistry()
    perm_rels = reg.by_category("Permutation")
    assert len(perm_rels) >= 2
    for r in perm_rels:
        assert r.category == "Permutation"

    idemp_rels = reg.by_category("Idempotence")
    assert len(idemp_rels) >= 1

    # Querying a non-existent relation returns None rather than raising an unhandled exception
    assert reg.get("MR_NON_EXISTENT_ID") is None

    # Summary list contains all registered relations
    summary = reg.get_summary()
    assert len(summary) >= 10
    assert any(item["id"] == "MR_REVERSE_INVARIANCE" for item in summary)


# ------------------------------------------------------------------------------
# 5. Engine: SafeExecutor In-Place Input Mutation Protection
# ------------------------------------------------------------------------------
def test_case_05_safe_executor_input_mutation_protection():
    """Test Case 5: Verifies SafeExecutor deep-copies inputs so buggy functions cannot mutate source data."""
    def in_place_mutator(arr):
        arr.append(999)
        return sorted(arr)

    original_input = [3, 2, 1]
    input_copy = copy.deepcopy(original_input)

    executor = SafeExecutor(timeout_seconds=1.0)
    res = executor.execute(in_place_mutator, original_input)
    assert res.success is True
    assert res.output == [1, 2, 3, 999]
    # Verify original_input was NOT mutated in-place by executor
    assert original_input == input_copy


# ------------------------------------------------------------------------------
# 6. Engine: SafeExecutor Dynamic Code Loading & Syntax Error Handling
# ------------------------------------------------------------------------------
def test_case_06_safe_executor_load_callable_from_code():
    """Test Case 6: Verifies dynamic loading of custom string code and syntax error rejection."""
    valid_code = """
def custom_multiply(items):
    return [x * 3 for x in items]
"""
    fn, detected_name = SafeExecutor.load_callable_from_code(valid_code)
    assert detected_name == "custom_multiply"
    assert fn([2, 4]) == [6, 12]

    # Malformed syntax code should raise SyntaxError or ValueError
    invalid_code = "def broken_syntax(: return 0"
    with pytest.raises((SyntaxError, ValueError)):
        SafeExecutor.load_callable_from_code(invalid_code)


# ------------------------------------------------------------------------------
# 7. Engine: InputGenerator Boundary and Edge Cases
# ------------------------------------------------------------------------------
def test_case_07_input_generator_boundary_and_edge_cases():
    """Test Case 7: Verifies InputGenerator boundary scenarios including negatives and duplicates."""
    gen = InputGenerator(seed=123)
    inputs = gen.generate_list_inputs(count=25)
    # Must include deterministic edge cases
    assert [] in inputs
    assert [0] in inputs or [1] in inputs
    assert any(len(x) > 1 and x[0] == x[1] for x in inputs if isinstance(x, list))
    assert any(any(val < 0 for val in x) for x in inputs if isinstance(x, list))


# ------------------------------------------------------------------------------
# 8. Database: Cascade Deletion of TestCases when TestRun is Deleted
# ------------------------------------------------------------------------------
def test_case_08_database_cascade_delete():
    """Test Case 8: Verifies deleting a TestRun cascades and deletes associated TestCases."""
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    try:
        run = TestRun(
            function_name="sample_fn",
            category="Sorting",
            variant="Ref",
            test_budget=10,
            status="PASSED",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Add 3 test cases
        for i in range(3):
            tc = TestCase(
                test_run_id=run.id,
                test_index=i,
                relation_id="MR_TEST",
                relation_name="Test Relation",
                passed=True,
            )
            db.add(tc)
        db.commit()

        assert db.query(TestCase).filter_by(test_run_id=run.id).count() == 3

        # Delete TestRun using service
        delete_test_run(db, run.id)

        # Assert all associated TestCases are purged
        assert db.query(TestCase).filter_by(test_run_id=run.id).count() == 0
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 9. Database: Test History Querying with Category and Status Filters
# ------------------------------------------------------------------------------
def test_case_09_database_test_history_filtering():
    """Test Case 9: Verifies get_test_history filters by status and category."""
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    try:
        run1 = TestRun(function_name="fn1", category="Sorting", variant="v1", status="PASSED")
        run2 = TestRun(function_name="fn2", category="Sorting", variant="v2", status="VIOLATED")
        run3 = TestRun(function_name="fn3", category="Shortest Path", variant="v3", status="PASSED")
        db.add_all([run1, run2, run3])
        db.commit()

        sorting_runs = get_test_history(db, category="Sorting")
        assert len(sorting_runs) == 2

        violated_runs = get_test_history(db, status="VIOLATED")
        assert len(violated_runs) == 1
        assert violated_runs[0].function_name == "fn2"

        path_passed = get_test_history(db, category="Shortest Path", status="PASSED")
        assert len(path_passed) == 1
        assert path_passed[0].function_name == "fn3"
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 10. Backend API: 404 Error Handling for Nonexistent Test Runs
# ------------------------------------------------------------------------------
def test_case_10_api_404_error_handling():
    """Test Case 10: Verifies GET /api/tests/{id} and DELETE /api/tests/{id} return 404 for missing IDs."""
    init_db()
    with TestClient(app) as client:
        # GET non-existent run
        res_get = client.get("/api/tests/999999")
        assert res_get.status_code == 404
        assert "not found" in res_get.json()["detail"].lower()

        # DELETE non-existent run
        res_del = client.delete("/api/tests/999999")
        assert res_del.status_code == 404
        assert "not found" in res_del.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 11. Backend API: Custom Metamorphic Relation Lifecycle (Create & Fetch)
# ------------------------------------------------------------------------------
def test_case_11_api_custom_relation_lifecycle():
    """Test Case 11: Verifies registering a custom relation via API and retrieving it."""
    init_db()
    with TestClient(app) as client:
        custom_payload = {
            "relation_id": "MR_CUSTOM_PARITY_CHECK",
            "name": "Parity Conservation Invariance",
            "category": "Parity",
            "formula": "sum(f(x)) % 2 == sum(x) % 2",
            "description": "Verifies sum parity conservation under sorting.",
        }
        res_create = client.post("/api/relations/custom", json=custom_payload)
        assert res_create.status_code == 200
        data = res_create.json()
        assert data["relation_id"] == "MR_CUSTOM_PARITY_CHECK"
        assert data["is_custom"] is True

        # Fetch it back by ID
        res_get = client.get("/api/relations/MR_CUSTOM_PARITY_CHECK")
        assert res_get.status_code == 200
        assert res_get.json()["name"] == "Parity Conservation Invariance"


# ------------------------------------------------------------------------------
# 12. Backend API: Code Snippet Lifecycle (Create, Get, and Delete)
# ------------------------------------------------------------------------------
def test_case_12_api_snippet_lifecycle():
    """Test Case 12: Verifies creating a snippet, retrieving it, and deleting it."""
    init_db()
    with TestClient(app) as client:
        snippet_payload = {
            "title": "Extended Lifecycle Snippet",
            "category": "Custom",
            "code": "def sample(x): return x[::-1]",
            "input_type": "list",
        }
        create_res = client.post("/api/snippets", json=snippet_payload)
        assert create_res.status_code == 200
        snip_id = create_res.json()["id"]

        # Confirm retrieval
        get_res = client.get(f"/api/snippets/{snip_id}")
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Extended Lifecycle Snippet"

        # Delete it
        del_res = client.delete(f"/api/snippets/{snip_id}")
        assert del_res.status_code == 200

        # Should now be 404
        subsequent_get = client.get(f"/api/snippets/{snip_id}")
        assert subsequent_get.status_code == 404


# ------------------------------------------------------------------------------
# 13. Evaluation: Benchmark Comparator Detection Breakdown
# ------------------------------------------------------------------------------
def test_case_13_benchmark_comparator_detailed_metrics():
    """Test Case 13: Verifies BenchmarkComparator accurately aggregates detected and missed bug names."""
    comparator = BenchmarkComparator(test_budget=15, seed=42)
    results = comparator.run_full_comparison()
    assert len(results) == 3

    random_res = results[0]
    unit_res = results[1]
    meta_res = results[2]

    # Verify attributes and types
    assert "Random Testing" in random_res.technique_name
    assert "MetaOracle" in meta_res.technique_name

    # Detection rate comparison
    assert meta_res.detection_rate >= unit_res.detection_rate
    assert meta_res.detection_rate > random_res.detection_rate
    assert len(meta_res.detected_bug_names) > 0
    assert isinstance(meta_res.missed_bug_names, list)
