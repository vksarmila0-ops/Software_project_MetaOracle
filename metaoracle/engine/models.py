"""
Data models for the MetaOracle testing engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class TestCaseResult:
    """Represents the execution and relation check of a single test case."""
    __test__ = False
    test_id: int
    relation_id: str
    relation_name: str
    source_input: Any
    follow_up_input: Any
    source_output: Any
    follow_up_output: Any
    passed: bool
    is_violation: bool
    is_error: bool
    error_message: Optional[str] = None
    violation_message: Optional[str] = None
    expected_relation: str = ""
    actual_observation: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "relation_id": self.relation_id,
            "relation_name": self.relation_name,
            "source_input": str(self.source_input),
            "follow_up_input": str(self.follow_up_input),
            "source_output": str(self.source_output),
            "follow_up_output": str(self.follow_up_output),
            "passed": self.passed,
            "is_violation": self.is_violation,
            "is_error": self.is_error,
            "error_message": self.error_message,
            "violation_message": self.violation_message,
            "expected_relation": self.expected_relation,
            "actual_observation": self.actual_observation,
            "duration_ms": round(self.duration_ms, 3),
        }


@dataclass
class RelationReport:
    """Summary of tests executed for a specific metamorphic relation."""
    relation_id: str
    relation_name: str
    total_tests: int = 0
    passed_tests: int = 0
    violated_tests: int = 0
    error_tests: int = 0
    test_cases: List[TestCaseResult] = field(default_factory=list)
    counterexamples: List[TestCaseResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return round((self.passed_tests / self.total_tests) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_name": self.relation_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "violated_tests": self.violated_tests,
            "error_tests": self.error_tests,
            "pass_rate": self.pass_rate,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "counterexamples_count": len(self.counterexamples),
            "counterexamples": [c.to_dict() for c in self.counterexamples[:10]],  # preview top 10
        }


@dataclass
class TestSuiteReport:
    """Comprehensive test report across all evaluated metamorphic relations."""
    __test__ = False
    target_function_name: str
    total_tests: int = 0
    passed_tests: int = 0
    violated_tests: int = 0
    error_tests: int = 0
    total_duration_ms: float = 0.0
    relation_reports: Dict[str, RelationReport] = field(default_factory=dict)
    all_counterexamples: List[TestCaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return round((self.passed_tests / self.total_tests) * 100.0, 2)

    @property
    def has_violations(self) -> bool:
        return self.violated_tests > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_function_name": self.target_function_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "violated_tests": self.violated_tests,
            "error_tests": self.error_tests,
            "pass_rate": self.pass_rate,
            "has_violations": self.has_violations,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "relation_reports": {k: v.to_dict() for k, v in self.relation_reports.items()},
            "counterexamples_summary": [c.to_dict() for c in self.all_counterexamples[:20]],
        }
