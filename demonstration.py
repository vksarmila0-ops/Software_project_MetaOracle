"""
MetaOracle End-to-End Demonstration Script.
Demonstrates the full 6-step project workflow:
1. Load a deliberately buggy sorting function.
2. Let MetaOracle recommend suitable metamorphic relations.
3. Generate inputs automatically (boundary & random).
4. Run testing engine and expose failing input pairs / counterexamples.
5. Perform AST mutation testing and display the measured mutation score.
6. Export the final test report (JSON).
"""

import json
import time
from metaoracle.sample_programs.sorting import sort_list_buggy_reverse
from metaoracle.suggestion.suggester import RelationSuggester
from metaoracle.engine.runner import MetamorphicTestRunner
from metaoracle.mutation.engine import MutationTester


def run_demonstration():
    print("=" * 80)
    print("      METAORACLE — END-TO-END DEMONSTRATION & DEFENSE WALKTHROUGH")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # Step 1: Deliberately Buggy Function
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Selected Target Function: sort_list_buggy_reverse")
    print("  Scenario: A developer introduced an optimization assuming descending inputs")
    print("  should return descending outputs, violating ascending sort specification.")
    print("  Problem: In traditional testing, without an oracle, we cannot verify outputs.")

    # --------------------------------------------------------------------------
    # Step 2: Automated Metamorphic Relation Recommendation
    # --------------------------------------------------------------------------
    print("\n[STEP 2] MetaOracle Static Heuristic & AST Suggestion Engine")
    suggester = RelationSuggester()
    suggestions = suggester.suggest_from_callable(sort_list_buggy_reverse)
    print(f"  Recommended {len(suggestions)} Metamorphic Relations:")
    for s in suggestions:
        print(f"    * [{s.confidence} Confidence] {s.relation.name}")
        print(f"      Rationale: {s.rationale}")

    active_relations = [s.relation for s in suggestions]

    # --------------------------------------------------------------------------
    # Step 3: Automatic Input Generation & Metamorphic Test Execution
    # --------------------------------------------------------------------------
    print("\n[STEP 3] Generating inputs automatically and running Metamorphic Engine...")
    runner = MetamorphicTestRunner(timeout_seconds=2.0, seed=42)
    test_count = 50
    report = runner.run_tests(
        target_func=sort_list_buggy_reverse,
        relations=active_relations,
        test_count=test_count,
        function_name="sort_list_buggy_reverse",
        input_type="list",
    )
    print(f"  Generated and tested {report.total_tests} metamorphic test cases across {test_count} inputs.")
    print(f"  Passed Tests: {report.passed_tests}")
    print(f"  Violations Found: {report.violated_tests}")
    print(f"  Pass Rate: {report.pass_rate:.1f}%")
    print(f"  Total Duration: {report.total_duration_ms:.2f} ms")

    # --------------------------------------------------------------------------
    # Step 4: Show Failing Input Pair & Explain Violated Relation
    # --------------------------------------------------------------------------
    print("\n[STEP 4] Defect Uncovered — Failing Input Pairs (Counterexamples)")
    if report.all_counterexamples:
        ce = report.all_counterexamples[0]
        print("  " + "-" * 70)
        print(f"  Violated Relation : {ce.relation_name}")
        print(f"  Source Input (x)  : {ce.source_input}")
        print(f"  Follow-up (x')    : {ce.follow_up_input}")
        print(f"  Source Output f(x): {ce.source_output}")
        print(f"  Follow-up f(x')   : {ce.follow_up_output}")
        print(f"  Diagnostic Reason : {ce.violation_message}")
        print("  " + "-" * 70)
        print("  EXPLANATION FOR EXAMINER:")
        print("  Notice that without computing the expected sorted list in advance,")
        print("  MetaOracle proved the program has a defect because reversing/permuting the")
        print("  input produced an inconsistent output order (ascending vs descending)!")
    else:
        print("  No violations detected.")

    # --------------------------------------------------------------------------
    # Step 5: Mutation Testing Analysis
    # --------------------------------------------------------------------------
    print("\n[STEP 5] Running AST Mutation Testing Analysis...")
    import inspect
    src_code = inspect.getsource(sort_list_buggy_reverse)
    mutation_tester = MutationTester(timeout_seconds=2.0, seed=42)
    mut_report = mutation_tester.run_mutation_analysis(
        source_code=src_code,
        relations=active_relations,
        test_count=30,
        max_mutants=10,
        input_type="list",
    )
    print(f"  Synthesized Mutants : {mut_report.total_mutants}")
    print(f"  Killed Mutants      : {mut_report.killed_mutants}")
    print(f"  Survived Mutants    : {mut_report.survived_mutants}")
    print(f"  Mutation Score      : {mut_report.mutation_score:.1f}%")
    if mut_report.relation_kill_breakdown:
        print("  Mutant Detection Breakdown by Metamorphic Relation:")
        for r_name, count in mut_report.relation_kill_breakdown.items():
            print(f"    - {r_name}: killed {count} mutants")

    # --------------------------------------------------------------------------
    # Step 6: Export the Test Report
    # --------------------------------------------------------------------------
    export_path = "demonstration_report.json"
    full_output = {
        "metadata": {
            "project": "MetaOracle",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target": "sort_list_buggy_reverse",
        },
        "test_suite_report": report.to_dict(),
        "mutation_report": mut_report.to_dict(),
    }
    with open(export_path, "w") as f:
        json.dump(full_output, f, indent=2)
    print(f"\n[STEP 6] Test report exported successfully to: {export_path}")
    print("\n" + "=" * 80)
    print("      DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_demonstration()
