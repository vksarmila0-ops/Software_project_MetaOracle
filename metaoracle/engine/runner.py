"""
Core Metamorphic Testing Runner for MetaOracle.
Executes source and follow-up inputs, compares outputs against metamorphic relations,
and gathers counterexamples and diagnostic metrics.
"""

import time
from typing import Any, Callable, Dict, List, Optional, Union
from .executor import SafeExecutor, ExecutionResult
from .generators import InputGenerator
from .models import TestCaseResult, RelationReport, TestSuiteReport
from ..relations.base import MetamorphicRelation


class MetamorphicTestRunner:
    """
    Orchestrates automated metamorphic test generation, execution, and verification.
    """

    def __init__(self, timeout_seconds: float = 2.0, seed: int = 42):
        self.timeout_seconds = timeout_seconds
        self.seed = seed
        self.executor = SafeExecutor(timeout_seconds=timeout_seconds)
        self.generator = InputGenerator(seed=seed)

    def run_tests(
        self,
        target_func: Union[Callable, str],
        relations: List[MetamorphicRelation],
        inputs: Optional[List[Any]] = None,
        test_count: int = 50,
        function_name: Optional[str] = None,
        input_type: str = "list",  # "list" or "graph"
    ) -> TestSuiteReport:
        """
        Runs metamorphic tests against target_func for all specified relations.
        """
        # Resolve target callable if string was passed
        if isinstance(target_func, str):
            callable_fn, detected_name = SafeExecutor.load_callable_from_code(
                target_func, function_name=function_name
            )
            fn_name = detected_name
        else:
            callable_fn = target_func
            fn_name = getattr(target_func, "__name__", "target_function")

        # Generate inputs if not provided
        if inputs is None:
            if input_type == "graph":
                inputs = self.generator.generate_graph_inputs(count=test_count)
            else:
                inputs = self.generator.generate_list_inputs(count=test_count)

        start_suite_time = time.perf_counter()
        suite_report = TestSuiteReport(target_function_name=fn_name)

        for relation in relations:
            rel_report = self._evaluate_relation(callable_fn, relation, inputs)
            suite_report.relation_reports[relation.relation_id] = rel_report
            suite_report.total_tests += rel_report.total_tests
            suite_report.passed_tests += rel_report.passed_tests
            suite_report.violated_tests += rel_report.violated_tests
            suite_report.error_tests += rel_report.error_tests
            suite_report.all_counterexamples.extend(rel_report.counterexamples)

        suite_report.total_duration_ms = (time.perf_counter() - start_suite_time) * 1000.0
        return suite_report

    def _evaluate_relation(
        self,
        target_fn: Callable,
        relation: MetamorphicRelation,
        test_inputs: List[Any],
    ) -> RelationReport:
        """Evaluates a single metamorphic relation across the test inputs."""
        rel_report = RelationReport(
            relation_id=relation.relation_id,
            relation_name=relation.name,
        )
        start_rel_time = time.perf_counter()

        for idx, src_input in enumerate(test_inputs, start=1):
            if relation.is_output_derived:
                # e.g. Idempotence: execute source x -> y, then execute follow-up y -> y'
                case_result = self._evaluate_output_derived_case(
                    target_fn, relation, src_input, test_id=idx
                )
            else:
                # Standard MR: transform x -> x', execute x -> y, x' -> y'
                case_result = self._evaluate_standard_case(
                    target_fn, relation, src_input, test_id=idx
                )

            rel_report.total_tests += 1
            rel_report.test_cases.append(case_result)

            if case_result.is_error:
                rel_report.error_tests += 1
            elif case_result.passed:
                rel_report.passed_tests += 1
            else:
                rel_report.violated_tests += 1
                rel_report.counterexamples.append(case_result)

        rel_report.total_duration_ms = (time.perf_counter() - start_rel_time) * 1000.0
        return rel_report

    def _evaluate_standard_case(
        self,
        target_fn: Callable,
        relation: MetamorphicRelation,
        source_input: Any,
        test_id: int,
    ) -> TestCaseResult:
        """Evaluates a standard MR: x -> x', then run both."""
        try:
            follow_up_input = relation.transform(source_input)
        except Exception as e:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=None,
                source_output=None,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Transformation error: {str(e)}",
            )

        # Execute source input
        res1 = self.executor.execute(target_fn, source_input)
        if not res1.success:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=follow_up_input,
                source_output=None,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Source execution failed: {res1.error_type}: {res1.error_message}",
                duration_ms=res1.duration_ms,
            )

        # Execute follow-up input
        res2 = self.executor.execute(target_fn, follow_up_input)
        if not res2.success:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=follow_up_input,
                source_output=res1.output,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Follow-up execution failed: {res2.error_type}: {res2.error_message}",
                duration_ms=res1.duration_ms + res2.duration_ms,
            )

        # Check relation
        check_res = relation.check(
            source_input=source_input,
            follow_up_input=follow_up_input,
            source_output=res1.output,
            follow_up_output=res2.output,
        )

        return TestCaseResult(
            test_id=test_id,
            relation_id=relation.relation_id,
            relation_name=relation.name,
            source_input=source_input,
            follow_up_input=follow_up_input,
            source_output=res1.output,
            follow_up_output=res2.output,
            passed=check_res.passed,
            is_violation=not check_res.passed,
            is_error=False,
            violation_message=check_res.message if not check_res.passed else None,
            expected_relation=check_res.expected_relation,
            actual_observation=check_res.actual_observation,
            duration_ms=res1.duration_ms + res2.duration_ms,
        )

    def _evaluate_output_derived_case(
        self,
        target_fn: Callable,
        relation: MetamorphicRelation,
        source_input: Any,
        test_id: int,
    ) -> TestCaseResult:
        """Evaluates an output-derived MR like Idempotence: x -> y, then y -> y'."""
        # 1. Run target on source x -> y
        res1 = self.executor.execute(target_fn, source_input)
        if not res1.success:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=None,
                source_output=None,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Source execution failed: {res1.error_type}: {res1.error_message}",
                duration_ms=res1.duration_ms,
            )

        # 2. Transform source output into follow-up input
        try:
            follow_up_input = relation.transform(res1.output)
        except Exception as e:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=None,
                source_output=res1.output,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Transformation error on output: {str(e)}",
            )

        # 3. Run target on follow-up input -> y'
        res2 = self.executor.execute(target_fn, follow_up_input)
        if not res2.success:
            return TestCaseResult(
                test_id=test_id,
                relation_id=relation.relation_id,
                relation_name=relation.name,
                source_input=source_input,
                follow_up_input=follow_up_input,
                source_output=res1.output,
                follow_up_output=None,
                passed=False,
                is_violation=False,
                is_error=True,
                error_message=f"Follow-up execution failed: {res2.error_type}: {res2.error_message}",
                duration_ms=res1.duration_ms + res2.duration_ms,
            )

        # 4. Check relation
        check_res = relation.check(
            source_input=source_input,
            follow_up_input=follow_up_input,
            source_output=res1.output,
            follow_up_output=res2.output,
        )

        return TestCaseResult(
            test_id=test_id,
            relation_id=relation.relation_id,
            relation_name=relation.name,
            source_input=source_input,
            follow_up_input=follow_up_input,
            source_output=res1.output,
            follow_up_output=res2.output,
            passed=check_res.passed,
            is_violation=not check_res.passed,
            is_error=False,
            violation_message=check_res.message if not check_res.passed else None,
            expected_relation=check_res.expected_relation,
            actual_observation=check_res.actual_observation,
            duration_ms=res1.duration_ms + res2.duration_ms,
        )
