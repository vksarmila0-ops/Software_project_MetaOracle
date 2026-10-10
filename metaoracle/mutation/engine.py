"""
Mutation Testing Engine for MetaOracle:
Executes the metamorphic test suite against generated mutants and computes the Mutation Score.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from .mutators import Mutant, MutantGenerator
from ..engine.runner import MetamorphicTestRunner
from ..engine.models import TestSuiteReport
from ..relations.base import MetamorphicRelation


@dataclass
class MutantEvaluationResult:
    """Outcome of testing a single mutant against the metamorphic relations."""
    mutant: Mutant
    status: str  # "KILLED", "SURVIVED", "ERROR"
    killing_relation_id: Optional[str] = None
    killing_relation_name: Optional[str] = None
    violation_message: Optional[str] = None
    failing_input: Optional[str] = None
    suite_report: Optional[TestSuiteReport] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutant_id": self.mutant.mutant_id,
            "operator": self.mutant.operator_name,
            "description": self.mutant.description,
            "line_number": self.mutant.line_number,
            "status": self.status,
            "killing_relation_id": self.killing_relation_id,
            "killing_relation_name": self.killing_relation_name,
            "violation_message": self.violation_message,
            "failing_input": self.failing_input,
            "diff": self.mutant.diff,
        }


@dataclass
class MutationTestSuiteReport:
    """Summary and metrics of mutation analysis."""
    target_function_name: str
    total_mutants: int = 0
    killed_mutants: int = 0
    survived_mutants: int = 0
    error_mutants: int = 0
    total_duration_ms: float = 0.0
    results: List[MutantEvaluationResult] = field(default_factory=list)
    relation_kill_breakdown: Dict[str, int] = field(default_factory=dict)

    @property
    def mutation_score(self) -> float:
        """
        Mutation Score = (Killed Mutants / Total Evaluated Mutants) * 100
        """
        if self.total_mutants == 0:
            return 0.0
        return round((self.killed_mutants / self.total_mutants) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_function_name": self.target_function_name,
            "total_mutants": self.total_mutants,
            "killed_mutants": self.killed_mutants,
            "survived_mutants": self.survived_mutants,
            "error_mutants": self.error_mutants,
            "mutation_score": self.mutation_score,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "relation_kill_breakdown": self.relation_kill_breakdown,
            "mutants": [r.to_dict() for r in self.results],
        }


class MutationTester:
    """Orchestrates mutant generation, execution, and mutation score calculation."""

    def __init__(self, timeout_seconds: float = 1.5, seed: int = 42):
        self.generator = MutantGenerator()
        self.runner = MetamorphicTestRunner(timeout_seconds=timeout_seconds, seed=seed)

    def run_mutation_analysis(
        self,
        source_code: str,
        relations: List[MetamorphicRelation],
        function_name: Optional[str] = None,
        test_inputs: Optional[List[Any]] = None,
        test_count: int = 30,
        max_mutants: int = 20,
        input_type: str = "list",
    ) -> MutationTestSuiteReport:
        """
        Generates mutants from source_code and evaluates them against the metamorphic test suite.
        """
        start_time = time.perf_counter()
        mutants = self.generator.generate_mutants(source_code, max_mutants=max_mutants)

        report = MutationTestSuiteReport(
            target_function_name=function_name or "target_function",
            total_mutants=len(mutants),
        )

        # Prepare test inputs once so all mutants are tested against identical inputs
        if test_inputs is None:
            if input_type == "graph":
                test_inputs = self.runner.generator.generate_graph_inputs(count=test_count)
            else:
                test_inputs = self.runner.generator.generate_list_inputs(count=test_count)

        for mutant in mutants:
            eval_result = self._evaluate_single_mutant(
                mutant=mutant,
                relations=relations,
                function_name=function_name,
                test_inputs=test_inputs,
                input_type=input_type,
            )
            report.results.append(eval_result)

            if eval_result.status == "KILLED":
                report.killed_mutants += 1
                if eval_result.killing_relation_name:
                    k_name = eval_result.killing_relation_name
                    report.relation_kill_breakdown[k_name] = (
                        report.relation_kill_breakdown.get(k_name, 0) + 1
                    )
            elif eval_result.status == "ERROR":
                # Runtime crash/exception also kills the mutant
                report.killed_mutants += 1
                report.error_mutants += 1
            else:
                report.survived_mutants += 1

        report.total_duration_ms = (time.perf_counter() - start_time) * 1000.0
        return report

    def _evaluate_single_mutant(
        self,
        mutant: Mutant,
        relations: List[MetamorphicRelation],
        function_name: Optional[str],
        test_inputs: List[Any],
        input_type: str,
    ) -> MutantEvaluationResult:
        """Runs the suite on a single mutant code."""
        try:
            suite_rep = self.runner.run_tests(
                target_func=mutant.mutated_code,
                relations=relations,
                inputs=test_inputs,
                function_name=function_name,
                input_type=input_type,
            )

            # Check if any relation caught a violation
            if suite_rep.violated_tests > 0:
                first_violation = suite_rep.all_counterexamples[0]
                return MutantEvaluationResult(
                    mutant=mutant,
                    status="KILLED",
                    killing_relation_id=first_violation.relation_id,
                    killing_relation_name=first_violation.relation_name,
                    violation_message=first_violation.violation_message,
                    failing_input=str(first_violation.source_input),
                    suite_report=suite_rep,
                )

            # Check if mutant triggered uncaught runtime crashes / errors
            if suite_rep.error_tests > 0:
                first_err = [
                    tc for rep in suite_rep.relation_reports.values()
                    for tc in rep.test_cases if tc.is_error
                ][0]
                return MutantEvaluationResult(
                    mutant=mutant,
                    status="KILLED",
                    killing_relation_id=first_err.relation_id,
                    killing_relation_name=first_err.relation_name,
                    violation_message=first_err.error_message,
                    failing_input=str(first_err.source_input),
                    suite_report=suite_rep,
                )

            # All tests passed without violation -> Mutant Survived
            return MutantEvaluationResult(
                mutant=mutant,
                status="SURVIVED",
                suite_report=suite_rep,
            )

        except Exception as e:
            # Fatal error compiling mutant or environment issue
            return MutantEvaluationResult(
                mutant=mutant,
                status="ERROR",
                violation_message=str(e),
            )
