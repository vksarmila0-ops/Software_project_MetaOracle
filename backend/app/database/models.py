"""
SQLAlchemy ORM models for MetaOracle database.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .session import Base


def utcnow():
    return datetime.now(timezone.utc)


class TestRun(Base):
    """Represents a completed or attempted metamorphic test suite run."""
    __tablename__ = "test_runs"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    function_name = Column(String(120), nullable=False)
    category = Column(String(80), default="General")
    variant = Column(String(120), default="Default")
    input_type = Column(String(50), default="list")
    test_budget = Column(Integer, default=50)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    violated_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    duration_ms = Column(Float, default=0.0)
    status = Column(String(50), default="PASSED")  # "PASSED", "VIOLATED", "ERROR"
    relation_summary = Column(Text, default="{}")  # JSON string of relation reports
    counterexamples_count = Column(Integer, default=0)
    source_code = Column(Text, nullable=True)

    # Relationship to detailed test cases
    cases = relationship("TestCase", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self, include_cases: bool = False):
        summary = {}
        if self.relation_summary:
            try:
                summary = json.loads(self.relation_summary)
            except Exception:
                summary = {}

        data = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "function_name": self.function_name,
            "category": self.category,
            "variant": self.variant,
            "input_type": self.input_type,
            "test_budget": self.test_budget,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "violated_tests": self.violated_tests,
            "error_tests": self.error_tests,
            "pass_rate": round(self.pass_rate, 2),
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "relation_summary": summary,
            "counterexamples_count": self.counterexamples_count,
            "source_code": self.source_code,
        }
        if include_cases:
            data["test_cases"] = [case.to_dict() for case in self.cases]
        return data


class TestCase(Base):
    """Detailed record of a single metamorphic test case execution."""
    __tablename__ = "test_cases"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_index = Column(Integer, default=0)
    relation_id = Column(String(80), nullable=False)
    relation_name = Column(String(120), nullable=False)
    source_input = Column(Text, default="")
    follow_up_input = Column(Text, default="")
    source_output = Column(Text, default="")
    follow_up_output = Column(Text, default="")
    passed = Column(Boolean, default=True)
    is_violation = Column(Boolean, default=False)
    is_error = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    violation_message = Column(Text, nullable=True)
    expected_relation = Column(Text, default="")
    actual_observation = Column(Text, default="")
    duration_ms = Column(Float, default=0.0)

    run = relationship("TestRun", back_populates="cases")

    def to_dict(self):
        return {
            "id": self.id,
            "test_run_id": self.test_run_id,
            "test_index": self.test_index,
            "relation_id": self.relation_id,
            "relation_name": self.relation_name,
            "source_input": self.source_input,
            "follow_up_input": self.follow_up_input,
            "source_output": self.source_output,
            "follow_up_output": self.follow_up_output,
            "passed": self.passed,
            "is_violation": self.is_violation,
            "is_error": self.is_error,
            "error_message": self.error_message,
            "violation_message": self.violation_message,
            "expected_relation": self.expected_relation,
            "actual_observation": self.actual_observation,
            "duration_ms": round(self.duration_ms, 3),
        }


class MutationRun(Base):
    """Record of an AST mutation testing execution."""
    __tablename__ = "mutation_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    function_name = Column(String(120), nullable=False)
    category = Column(String(80), default="General")
    total_mutants = Column(Integer, default=0)
    killed_mutants = Column(Integer, default=0)
    survived_mutants = Column(Integer, default=0)
    error_mutants = Column(Integer, default=0)
    mutation_score = Column(Float, default=0.0)
    duration_ms = Column(Float, default=0.0)
    results_json = Column(Text, default="[]")  # List of mutant details & diffs

    def to_dict(self):
        details = []
        if self.results_json:
            try:
                details = json.loads(self.results_json)
            except Exception:
                details = []

        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "function_name": self.function_name,
            "category": self.category,
            "total_mutants": self.total_mutants,
            "killed_mutants": self.killed_mutants,
            "survived_mutants": self.survived_mutants,
            "error_mutants": self.error_mutants,
            "mutation_score": round(self.mutation_score, 2),
            "duration_ms": round(self.duration_ms, 2),
            "mutants": details,
        }


class BenchmarkRun(Base):
    """Record of Phase 6 comparative evaluation comparing 3 paradigms."""
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    test_budget = Column(Integer, default=50)
    total_scenarios = Column(Integer, default=7)
    results_json = Column(Text, default="[]")  # Array of TechniqueResult dicts
    summary_notes = Column(Text, nullable=True)

    def to_dict(self):
        results = []
        if self.results_json:
            try:
                results = json.loads(self.results_json)
            except Exception:
                results = []

        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "test_budget": self.test_budget,
            "total_scenarios": self.total_scenarios,
            "results": results,
            "summary_notes": self.summary_notes,
        }


class CustomRelation(Base):
    """User-defined or persistent Metamorphic Relation."""
    __tablename__ = "custom_relations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    relation_id = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(80), default="Custom")
    formula = Column(String(200), default="")
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "relation_id": self.relation_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "formula": self.formula,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeSnippet(Base):
    """Saved custom Python code snippets for testing."""
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(120), nullable=False)
    category = Column(String(80), default="Custom")
    code = Column(Text, nullable=False)
    input_type = Column(String(50), default="list")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "code": self.code,
            "input_type": self.input_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
