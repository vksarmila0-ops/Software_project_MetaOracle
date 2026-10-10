"""
Service orchestrating metamorphic test runs and database persistence.
"""

import json
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from metaoracle.engine.runner import MetamorphicTestRunner
from metaoracle.engine.models import TestSuiteReport, TestCaseResult
from metaoracle.relations.registry import default_registry
from ..database.models import TestRun, TestCase
from .preset_registry import (
    get_preset_function,
    get_preset_input_type,
    get_preset_code,
)
from .suggester_service import suggest_relations_for_target


def execute_test_suite(
    db: Session,
    category: str,
    variant: str,
    custom_code: Optional[str] = None,
    input_type: Optional[str] = None,
    selected_relation_ids: Optional[List[str]] = None,
    test_budget: int = 50,
    seed: int = 42,
) -> TestRun:
    """
    Executes a metamorphic test run, evaluates relations, and persists results to SQLite.
    """
    # 1. Resolve target callable or source code
    target_code = None
    if category == "Custom Python Code" or (custom_code and custom_code.strip()):
        target = custom_code or get_preset_code("Sorting", "Correct Reference")
        fn_name = "custom_function"
        resolved_input_type = input_type or "list"
        target_code = target
    else:
        target = get_preset_function(category, variant)
        if target is None:
            # Fallback to sorting correct
            target = get_preset_function("Sorting", "Correct Reference")
            fn_name = "sort_list"
        else:
            fn_name = target.__name__
        resolved_input_type = input_type or get_preset_input_type(category, variant)
        target_code = get_preset_code(category, variant)

    # 2. Resolve Metamorphic Relations
    active_relations = []
    if selected_relation_ids and len(selected_relation_ids) > 0:
        for rid in selected_relation_ids:
            rel = default_registry.get(rid)
            if rel:
                active_relations.append(rel)
    
    # If no relations selected, use suggester to automatically pick
    if not active_relations:
        suggestions_res = suggest_relations_for_target(
            category=category,
            variant=variant,
            custom_code=custom_code,
        )
        for s in suggestions_res["suggestions"]:
            rel = default_registry.get(s["relation_id"])
            if rel:
                active_relations.append(rel)

    # If still none, fallback to default first 2
    if not active_relations:
        active_relations = default_registry.list_all()[:2]

    # 3. Execute Metamorphic Testing
    runner = MetamorphicTestRunner(timeout_seconds=3.0, seed=seed)
    suite_report: TestSuiteReport = runner.run_tests(
        target_func=target,
        relations=active_relations,
        test_count=test_budget,
        function_name=fn_name,
        input_type=resolved_input_type,
    )

    # 4. Determine overall status
    if suite_report.violated_tests > 0:
        run_status = "VIOLATED"
    elif suite_report.error_tests > 0 and suite_report.passed_tests == 0:
        run_status = "ERROR"
    else:
        run_status = "PASSED"

    # Prepare relation summary dict
    rel_summary = {
        rid: r_rep.to_dict()
        for rid, r_rep in suite_report.relation_reports.items()
    }

    # 5. Persist TestRun into Database
    test_run_record = TestRun(
        function_name=fn_name,
        category=category,
        variant=variant,
        input_type=resolved_input_type,
        test_budget=test_budget,
        total_tests=suite_report.total_tests,
        passed_tests=suite_report.passed_tests,
        violated_tests=suite_report.violated_tests,
        error_tests=suite_report.error_tests,
        pass_rate=suite_report.pass_rate,
        duration_ms=suite_report.total_duration_ms,
        status=run_status,
        relation_summary=json.dumps(rel_summary),
        counterexamples_count=len(suite_report.all_counterexamples),
        source_code=target_code,
    )
    db.add(test_run_record)
    db.commit()
    db.refresh(test_run_record)

    # 6. Persist Test Cases:
    # Always persist ALL counterexamples, plus a sample of passed cases
    cases_to_persist = []
    
    # All counterexamples first
    for idx, ce in enumerate(suite_report.all_counterexamples):
        cases_to_persist.append(
            TestCase(
                test_run_id=test_run_record.id,
                test_index=ce.test_id,
                relation_id=ce.relation_id,
                relation_name=ce.relation_name,
                source_input=str(ce.source_input),
                follow_up_input=str(ce.follow_up_input),
                source_output=str(ce.source_output),
                follow_up_output=str(ce.follow_up_output),
                passed=ce.passed,
                is_violation=ce.is_violation,
                is_error=ce.is_error,
                error_message=ce.error_message,
                violation_message=ce.violation_message,
                expected_relation=ce.expected_relation,
                actual_observation=ce.actual_observation,
                duration_ms=ce.duration_ms,
            )
        )

    # Collect up to 20 passed cases across relations for balanced auditing
    passed_count = 0
    for r_rep in suite_report.relation_reports.values():
        for tc in r_rep.test_cases:
            if tc.passed and passed_count < 20:
                cases_to_persist.append(
                    TestCase(
                        test_run_id=test_run_record.id,
                        test_index=tc.test_id,
                        relation_id=tc.relation_id,
                        relation_name=tc.relation_name,
                        source_input=str(tc.source_input),
                        follow_up_input=str(tc.follow_up_input),
                        source_output=str(tc.source_output),
                        follow_up_output=str(tc.follow_up_output),
                        passed=tc.passed,
                        is_violation=tc.is_violation,
                        is_error=tc.is_error,
                        error_message=tc.error_message,
                        violation_message=tc.violation_message,
                        expected_relation=tc.expected_relation,
                        actual_observation=tc.actual_observation,
                        duration_ms=tc.duration_ms,
                    )
                )
                passed_count += 1

    if cases_to_persist:
        db.bulk_save_objects(cases_to_persist)
        db.commit()

    return test_run_record


def get_test_history(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> List[TestRun]:
    """Retrieves paginated test runs with optional filters."""
    query = db.query(TestRun)
    if category:
        query = query.filter(TestRun.category == category)
    if status:
        query = query.filter(TestRun.status == status)
    return query.order_by(TestRun.created_at.desc()).offset(offset).limit(limit).all()


def get_test_run_details(db: Session, run_id: int) -> Optional[TestRun]:
    """Fetches a specific test run and all its recorded test cases."""
    return db.query(TestRun).filter(TestRun.id == run_id).first()


def delete_test_run(db: Session, run_id: int) -> bool:
    """Deletes a test run and its associated test cases."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        return False
    db.delete(run)
    db.commit()
    return True
