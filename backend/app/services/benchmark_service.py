"""
Service for running and storing Phase 6 Comparative Empirical Benchmarks.
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from metaoracle.evaluation.comparator import BenchmarkComparator
from ..database.models import BenchmarkRun


def execute_benchmark(db: Session, budget: int = 50) -> BenchmarkRun:
    """
    Executes head-to-head empirical comparison across Random, Unit, and Metamorphic testing.
    Saves the comparative run into the SQLite database.
    """
    comparator = BenchmarkComparator(test_budget=budget, seed=42)
    results = comparator.run_full_comparison()

    results_data = [r.to_dict() for r in results]

    summary = (
        f"Benchmark evaluated {len(results)} testing paradigms across 7 seeded bugs "
        f"with budget of {budget} inputs per bug. "
        f"Random Testing detection rate: {results[0].detection_rate}%. "
        f"Expected-Output Unit Testing detection rate: {results[1].detection_rate}%. "
        f"MetaOracle Metamorphic Testing detection rate: {results[2].detection_rate}%."
    )

    record = BenchmarkRun(
        test_budget=budget,
        total_scenarios=7,
        results_json=json.dumps(results_data),
        summary_notes=summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def get_benchmark_history(db: Session, limit: int = 10) -> List[BenchmarkRun]:
    """Returns past benchmark runs from database."""
    return db.query(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()).limit(limit).all()


def get_benchmark_details(db: Session, run_id: int) -> Optional[BenchmarkRun]:
    """Returns a specific benchmark run by ID."""
    return db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
