"""
API Router for overall system statistics and executive dashboard metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database.session import get_db
from ..database.models import TestRun, TestCase, MutationRun, BenchmarkRun, CustomRelation, CodeSnippet
from ..schemas.pydantic_models import DashboardStatsResponse

router = APIRouter(prefix="/api/stats", tags=["System Statistics"])


@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Computes real-time aggregate metrics across all historical test runs, mutations, and relations.
    """
    total_runs = db.query(func.count(TestRun.id)).scalar() or 0
    total_tests = db.query(func.sum(TestRun.total_tests)).scalar() or 0
    total_violations = db.query(func.sum(TestRun.violated_tests)).scalar() or 0
    
    # Pass rate
    total_passed = db.query(func.sum(TestRun.passed_tests)).scalar() or 0
    overall_pass_rate = 0.0
    if total_tests > 0:
        overall_pass_rate = round((total_passed / total_tests) * 100.0, 2)

    # Mutation stats
    total_mutations = db.query(func.count(MutationRun.id)).scalar() or 0
    avg_mutation_score = db.query(func.avg(MutationRun.mutation_score)).scalar() or 0.0

    # Custom counts
    total_custom_rels = db.query(func.count(CustomRelation.id)).scalar() or 0
    total_snippets = db.query(func.count(CodeSnippet.id)).scalar() or 0

    # Recent 6 runs
    recent_runs = (
        db.query(TestRun)
        .order_by(TestRun.created_at.desc())
        .limit(6)
        .all()
    )

    return {
        "total_runs": total_runs,
        "total_tests_executed": total_tests,
        "total_violations_detected": total_violations,
        "overall_pass_rate": overall_pass_rate,
        "recent_runs": [r.to_dict(include_cases=False) for r in recent_runs],
        "total_mutations_run": total_mutations,
        "avg_mutation_score": round(float(avg_mutation_score), 2),
        "total_custom_relations": total_custom_rels,
        "total_snippets": total_snippets,
    }
