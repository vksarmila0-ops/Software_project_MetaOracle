"""
MetaOracle Command-Line Interface (CLI).
Enables running metamorphic tests, mutation testing, and comparative benchmarks directly from terminal.
"""

import argparse
import json
import sys
from typing import List

from .engine.runner import MetamorphicTestRunner
from .mutation.engine import MutationTester
from .evaluation.comparator import BenchmarkComparator
from .suggestion.suggester import RelationSuggester
from .relations.registry import default_registry
from .sample_programs.sorting import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
    sort_list_buggy_partial,
)
from .sample_programs.shortest_route import (
    shortest_route,
    shortest_route_buggy_asymmetric,
    shortest_route_buggy_weight,
)
from .sample_programs.duplicate_removal import (
    remove_duplicates,
    remove_duplicates_buggy_consecutive,
    remove_duplicates_buggy_idempotence,
)


def get_target_function(name: str, variant: str):
    name = name.lower()
    variant = variant.lower()

    if "sort" in name:
        if "rev" in variant:
            return sort_list_buggy_reverse, "sort_list (Buggy Reverse)", "list"
        elif "dup" in variant:
            return sort_list_buggy_duplicates, "sort_list (Buggy Duplicates)", "list"
        elif "part" in variant:
            return sort_list_buggy_partial, "sort_list (Buggy Partial)", "list"
        else:
            return sort_list, "sort_list (Correct Reference)", "list"

    elif "route" in name or "graph" in name or "path" in name:
        if "asym" in variant:
            return shortest_route_buggy_asymmetric, "shortest_route (Buggy Asymmetric)", "graph"
        elif "weight" in variant:
            return shortest_route_buggy_weight, "shortest_route (Buggy Weight)", "graph"
        else:
            return shortest_route, "shortest_route (Correct Reference)", "graph"

    elif "dedup" in name or "dup" in name or "remove" in name:
        if "consec" in variant:
            return remove_duplicates_buggy_consecutive, "remove_duplicates (Buggy Consecutive)", "list"
        elif "idem" in variant:
            return remove_duplicates_buggy_idempotence, "remove_duplicates (Buggy Idempotence)", "list"
        else:
            return remove_duplicates, "remove_duplicates (Correct Reference)", "list"

    raise ValueError(f"Unknown function: {name} with variant: {variant}")


def main():
    parser = argparse.ArgumentParser(
        description="MetaOracle: Oracle-Free Testing Using Metamorphic Relations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--function",
        type=str,
        default="sort_list",
        choices=["sort_list", "shortest_route", "remove_duplicates"],
        help="Target function to test",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="buggy_reverse",
        help="Variant: correct, buggy_reverse, buggy_duplicates, buggy_asymmetric, buggy_idempotence, etc.",
    )
    parser.add_argument(
        "--tests",
        type=int,
        default=50,
        help="Number of metamorphic test inputs to generate",
    )
    parser.add_argument(
        "--mutation",
        action="store_true",
        help="Run mutation testing analysis",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run Phase 6 comparative evaluation against Random and Unit testing",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="",
        help="Filepath to export test results as JSON",
    )

    args = parser.parse_args()

    print("=" * 72)
    print("  METAORACLE — Oracle-Free Testing Using Metamorphic Relations")
    print("=" * 72)

    if args.evaluate:
        print("\n[*] Running Phase 6 Comparative Evaluation across testing paradigms...")
        comparator = BenchmarkComparator(test_budget=args.tests)
        results = comparator.run_full_comparison()

        print("\n" + "-" * 72)
        print(f"{'Testing Technique':<32} | {'Detection Rate':<15} | {'Runtime (ms)':<12}")
        print("-" * 72)
        for r in results:
            print(f"{r.technique_name:<32} | {r.detection_rate:>13.1f}% | {r.duration_ms:>10.2f} ms")
        print("-" * 72)

        for r in results:
            print(f"\n[{r.technique_name}]")
            print(f"  Oracle: {r.oracle_type}")
            print(f"  Effort: {r.oracle_effort}")
            print(f"  Bugs Caught: {r.detected_bugs_count}/{r.total_evaluated_bugs} ({r.detected_bug_names})")
            if r.missed_bug_names:
                print(f"  Missed: {r.missed_bug_names}")
            print(f"  Notes: {r.notes}")
        return

    # Normal Metamorphic Test Run
    target_fn, display_name, input_type = get_target_function(args.function, args.variant)
    print(f"\n[+] Target Function : {display_name}")
    print(f"[+] Test Input Type : {input_type}")
    print(f"[+] Test Budget     : {args.tests} inputs")

    # Get suggested relations
    suggester = RelationSuggester()
    suggestions = suggester.suggest_from_callable(target_fn)
    selected_relations = [s.relation for s in suggestions]

    if not selected_relations:
        selected_relations = default_registry.list_all()

    print(f"\n[+] Active Metamorphic Relations ({len(selected_relations)}):")
    for s in suggestions:
        print(f"    - [{s.confidence}] {s.relation.name}: {s.rationale}")

    # Run tests
    print(f"\n[*] Generating inputs and executing metamorphic test engine...")
    runner = MetamorphicTestRunner(seed=42)
    report = runner.run_tests(
        target_func=target_fn,
        relations=selected_relations,
        test_count=args.tests,
        function_name=args.function,
        input_type=input_type,
    )

    print("\n" + "=" * 72)
    print("  TEST EXECUTION RESULTS")
    print("=" * 72)
    print(f"Total Tests Executed : {report.total_tests}")
    print(f"Passed Tests         : {report.passed_tests}")
    print(f"Violations Detected  : {report.violated_tests}")
    print(f"Execution Time       : {report.total_duration_ms:.2f} ms")
    print(f"Pass Rate            : {report.pass_rate:.1f}%")

    print("\n[+] Breakdown by Metamorphic Relation:")
    for rel_id, rel_rep in report.relation_reports.items():
        status = "PASSED" if rel_rep.violated_tests == 0 else f"VIOLATED ({rel_rep.violated_tests} violations)"
        print(f"  - {rel_rep.relation_name:<38}: {status}")

    if report.all_counterexamples:
        print("\n" + "!" * 72)
        print("  REPRODUCIBLE BUG DETECTED: FAILING COUNTEREXAMPLES")
        print("!" * 72)
        for i, ce in enumerate(report.all_counterexamples[:3], 1):
            print(f"\nCounterexample #{i}: [{ce.relation_name}]")
            print(f"  Source Input     : {ce.source_input}")
            print(f"  Transformed Input: {ce.follow_up_input}")
            print(f"  Source Output    : {ce.source_output}")
            print(f"  Follow-up Output : {ce.follow_up_output}")
            print(f"  Violation Note   : {ce.violation_message}")

    if args.mutation:
        import inspect
        src_code = inspect.getsource(target_fn)
        print("\n" + "=" * 72)
        print("  PHASE 4: MUTATION TESTING ANALYSIS")
        print("=" * 72)
        tester = MutationTester()
        mut_report = tester.run_mutation_analysis(
            source_code=src_code,
            relations=selected_relations,
            function_name=args.function,
            test_count=min(args.tests, 30),
            max_mutants=15,
            input_type=input_type,
        )
        print(f"Total Mutants Generated : {mut_report.total_mutants}")
        print(f"Killed Mutants          : {mut_report.killed_mutants}")
        print(f"Survived Mutants        : {mut_report.survived_mutants}")
        print(f"Measured Mutation Score : {mut_report.mutation_score:.1f}%")

        if mut_report.relation_kill_breakdown:
            print("\n  Relation Kill Breakdown:")
            for r_name, count in mut_report.relation_kill_breakdown.items():
                print(f"    * {r_name}: killed {count} mutants")

    if args.export:
        with open(args.export, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n[+] Exported test report to {args.export}")


if __name__ == "__main__":
    main()
