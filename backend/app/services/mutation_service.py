"""
Service for executing AST mutation analysis and recording results in the database.
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from metaoracle.mutation.engine import MutationTester
from metaoracle.relations.registry import default_registry
from ..database.models import MutationRun
from .preset_registry import (
    get_preset_function,
    get_preset_code,
    get_preset_input_type,
)
from .suggester_service import suggest_relations_for_target


def execute_mutation_analysis(
    db: Session,
    category: str,
    variant: str,
    custom_code: Optional[str] = None,
    test_budget: int = 30,
    selected_relation_ids: Optional[List[str]] = None,
) -> MutationRun:
    """
    Executes AST mutation analysis on the target function and saves run to SQLite.
    """
    # 1. Resolve source code
    if category == "Custom Python Code" or (custom_code and custom_code.strip()):
        source_code = custom_code or get_preset_code("Sorting", "Correct Reference")
        fn_name = "custom_function"
        input_type = "list"
    else:
        source_code = get_preset_code(category, variant)
        fn = get_preset_function(category, variant)
        fn_name = fn.__name__ if fn else "target_function"
        input_type = get_preset_input_type(category, variant)

    # 2. Resolve relations
    active_relations = []
    if selected_relation_ids:
        for rid in selected_relation_ids:
            rel = default_registry.get(rid)
            if rel:
                active_relations.append(rel)

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

    if not active_relations:
        active_relations = default_registry.list_all()[:3]

    # 3. Execute Mutation Testing
    tester = MutationTester(timeout_seconds=2.0, seed=42)
    report = tester.run_mutation_analysis(
        source_code=source_code,
        relations=active_relations,
        function_name=fn_name,
        test_count=test_budget,
        max_mutants=15,
        input_type=input_type,
    )

    # 4. Serialize mutant records
    mutant_dicts = [r.to_dict() for r in report.results]

    # 5. Persist to DB
    mutation_record = MutationRun(
        function_name=fn_name,
        category=category,
        total_mutants=report.total_mutants,
        killed_mutants=report.killed_mutants,
        survived_mutants=report.survived_mutants,
        error_mutants=report.error_mutants,
        mutation_score=report.mutation_score,
        duration_ms=report.total_duration_ms,
        results_json=json.dumps(mutant_dicts),
    )
    db.add(mutation_record)
    db.commit()
    db.refresh(mutation_record)

    return mutation_record


def get_mutation_history(db: Session, limit: int = 20) -> List[MutationRun]:
    """Returns past mutation testing runs."""
    return db.query(MutationRun).order_by(MutationRun.created_at.desc()).limit(limit).all()


def get_mutation_run_details(db: Session, run_id: int) -> Optional[MutationRun]:
    """Fetches a specific mutation run by ID."""
    return db.query(MutationRun).filter(MutationRun.id == run_id).first()
