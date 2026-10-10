"""
API Router for AST Mutation Testing.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.pydantic_models import RunMutationRequest, MutationRunResponse
from ..services.mutation_service import (
    execute_mutation_analysis,
    get_mutation_history,
    get_mutation_run_details,
)

router = APIRouter(prefix="/api/mutation", tags=["Mutation Testing"])


@router.post("/run", response_model=MutationRunResponse)
def run_mutation_test(request: RunMutationRequest, db: Session = Depends(get_db)):
    """
    Synthesizes AST mutants, runs metamorphic tests against them, and calculates the mutation score.
    Persists the run and mutant diffs in the database.
    """
    try:
        run_record = execute_mutation_analysis(
            db=db,
            category=request.category,
            variant=request.variant,
            custom_code=request.custom_code,
            test_budget=request.test_budget,
            selected_relation_ids=request.selected_relation_ids,
        )
        return run_record.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mutation testing error: {str(e)}")


@router.get("/history", response_model=List[MutationRunResponse])
def list_mutation_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieves previous mutation testing runs from the database.
    """
    runs = get_mutation_history(db=db, limit=limit)
    return [r.to_dict() for r in runs]


@router.get("/{run_id}", response_model=MutationRunResponse)
def get_mutation_run(run_id: int, db: Session = Depends(get_db)):
    """
    Retrieves details and mutant diffs for a specific mutation run.
    """
    run = get_mutation_run_details(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Mutation run not found")
    return run.to_dict()
