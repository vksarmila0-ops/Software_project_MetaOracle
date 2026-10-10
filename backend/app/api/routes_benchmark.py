"""
API Router for Phase 6 Comparative Empirical Benchmark.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.pydantic_models import RunBenchmarkRequest, BenchmarkRunResponse
from ..services.benchmark_service import (
    execute_benchmark,
    get_benchmark_history,
    get_benchmark_details,
)

router = APIRouter(prefix="/api/benchmark", tags=["Empirical Benchmark"])


@router.post("/run", response_model=BenchmarkRunResponse)
def run_benchmark(request: RunBenchmarkRequest, db: Session = Depends(get_db)):
    """
    Executes a Phase 6 empirical comparison benchmark comparing:
    1. Random Testing (Crash-Only Oracle)
    2. Conventional Unit Testing (Handcrafted assertions)
    3. MetaOracle Metamorphic Testing (Oracle-Free)
    Persists evaluation outcome in SQLite.
    """
    try:
        record = execute_benchmark(db=db, budget=request.budget)
        return record.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Benchmark execution failed: {str(e)}")


@router.get("/history", response_model=List[BenchmarkRunResponse])
def list_benchmark_runs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieves previous empirical benchmark runs from the database.
    """
    runs = get_benchmark_history(db=db, limit=limit)
    return [r.to_dict() for r in runs]


@router.get("/{run_id}", response_model=BenchmarkRunResponse)
def get_benchmark(run_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific benchmark run by ID.
    """
    run = get_benchmark_details(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return run.to_dict()
