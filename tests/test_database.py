"""
Unit tests for MetaOracle SQLite database models and ORM operations.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.database.models import (
    TestRun,
    TestCase,
    MutationRun,
    BenchmarkRun,
    CustomRelation,
    CodeSnippet,
)


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite database for isolated unit tests."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_test_run_and_cases(test_db):
    """Verifies creating a TestRun and nested TestCases."""
    run = TestRun(
        function_name="sort_list_buggy_reverse",
        category="Sorting",
        variant="Bug: Reverse Input Bias",
        input_type="list",
        test_budget=20,
        total_tests=20,
        passed_tests=15,
        violated_tests=5,
        pass_rate=75.0,
        duration_ms=120.5,
        status="VIOLATED",
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)

    assert run.id is not None
    assert run.pass_rate == 75.0

    # Add a test case
    case = TestCase(
        test_run_id=run.id,
        test_index=1,
        relation_id="MR_REVERSE_INVARIANCE",
        relation_name="Reverse-Input Invariance",
        source_input="[3, 2, 1]",
        follow_up_input="[1, 2, 3]",
        source_output="[3, 2, 1]",
        follow_up_output="[1, 2, 3]",
        passed=False,
        is_violation=True,
        violation_message="Output mismatch: [3, 2, 1] != [1, 2, 3]",
    )
    test_db.add(case)
    test_db.commit()
    test_db.refresh(case)

    assert case.id is not None
    assert len(run.cases) == 1

    d = run.to_dict(include_cases=True)
    assert d["function_name"] == "sort_list_buggy_reverse"
    assert len(d["test_cases"]) == 1


def test_mutation_run_persistence(test_db):
    """Verifies storing and retrieving MutationRun."""
    m_run = MutationRun(
        function_name="sort_list",
        category="Sorting",
        total_mutants=10,
        killed_mutants=8,
        survived_mutants=2,
        error_mutants=0,
        mutation_score=80.0,
        duration_ms=250.0,
        results_json="[]",
    )
    test_db.add(m_run)
    test_db.commit()
    test_db.refresh(m_run)

    assert m_run.id is not None
    assert m_run.mutation_score == 80.0


def test_benchmark_run_persistence(test_db):
    """Verifies storing BenchmarkRun."""
    b_run = BenchmarkRun(
        test_budget=50,
        total_scenarios=7,
        results_json="[]",
        summary_notes="Empirical test benchmark",
    )
    test_db.add(b_run)
    test_db.commit()
    test_db.refresh(b_run)

    assert b_run.id is not None
    assert b_run.total_scenarios == 7


def test_custom_relation_and_snippet(test_db):
    """Verifies custom relation and code snippet persistence."""
    rel = CustomRelation(
        relation_id="MR_CUSTOM_TEST",
        name="Custom Test Relation",
        description="Verifies user invariant",
        category="Custom",
        formula="f(2*x) == 2*f(x)",
    )
    test_db.add(rel)

    snippet = CodeSnippet(
        title="Custom QuickSort",
        category="Sorting",
        code="def qsort(arr): return sorted(arr)",
        input_type="list",
    )
    test_db.add(snippet)
    test_db.commit()

    saved_rel = test_db.query(CustomRelation).filter_by(relation_id="MR_CUSTOM_TEST").first()
    assert saved_rel is not None
    assert saved_rel.name == "Custom Test Relation"

    saved_snip = test_db.query(CodeSnippet).filter_by(title="Custom QuickSort").first()
    assert saved_snip is not None
    assert saved_snip.input_type == "list"
