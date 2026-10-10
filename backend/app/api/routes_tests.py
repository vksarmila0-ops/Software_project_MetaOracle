"""
API Router for Metamorphic Test executions and history.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.pydantic_models import RunTestRequest, TestRunResponse
from ..services.test_service import (
    execute_test_suite,
    get_test_history,
    get_test_run_details,
    delete_test_run,
)
from ..services.preset_registry import list_all_presets, get_preset_code

router = APIRouter(prefix="/api/tests", tags=["Metamorphic Testing"])


@router.post("/run", response_model=TestRunResponse)
def run_tests(request: RunTestRequest, db: Session = Depends(get_db)):
    """
    Executes a metamorphic test run across selected or auto-suggested relations.
    Stores the run and counterexample cases into the database.
    """
    try:
        run_record = execute_test_suite(
            db=db,
            category=request.category,
            variant=request.variant,
            custom_code=request.custom_code,
            input_type=request.input_type,
            selected_relation_ids=request.selected_relation_ids,
            test_budget=request.test_budget,
            seed=request.seed or 42,
        )
        return run_record.to_dict(include_cases=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution error: {str(e)}")


@router.get("/history", response_model=List[TestRunResponse])
def list_history(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (PASSED, VIOLATED, ERROR)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieves chronological test execution history from the database.
    """
    runs = get_test_history(db=db, limit=limit, offset=offset, category=category, status=status)
    return [r.to_dict(include_cases=False) for r in runs]


@router.get("/presets")
def get_presets():
    """
    Returns the catalog of available preset algorithms and seeded bug variants.
    """
    presets = list_all_presets()
    # Enrich with source code for easy client loading
    for p in presets:
        p["code"] = get_preset_code(p["category"], p["variant"])
    return presets


@router.get("/{run_id}", response_model=TestRunResponse)
def get_test_run(run_id: int, db: Session = Depends(get_db)):
    """
    Fetches full details and counterexamples for a specific test run.
    """
    run = get_test_run_details(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run.to_dict(include_cases=True)


@router.delete("/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """
    Deletes a test run and its recorded test cases from the database.
    """
    success = delete_test_run(db=db, run_id=run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test run not found")
    return {"message": "Test run deleted successfully", "id": run_id}
