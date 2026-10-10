"""
MetaOracle — Oracle-Free Testing Using Metamorphic Relations.
Interactive Streamlit Web Dashboard and Testing Studio.
"""

import ast
import inspect
import json
import os
import sys
import time
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from metaoracle.relations.registry import default_registry
from metaoracle.suggestion.suggester import RelationSuggester
from metaoracle.engine.runner import MetamorphicTestRunner
from metaoracle.engine.executor import SafeExecutor
from metaoracle.mutation.engine import MutationTester
from metaoracle.evaluation.comparator import BenchmarkComparator
from metaoracle.sample_programs import (
    sort_list,
    sort_list_buggy_reverse,
    sort_list_buggy_duplicates,
    sort_list_buggy_partial,
    shortest_route,
    shortest_route_buggy_asymmetric,
    shortest_route_buggy_weight,
    remove_duplicates,
    remove_duplicates_buggy_consecutive,
    remove_duplicates_buggy_idempotence,
)

# Page configuration
st.set_page_config(
    page_title="MetaOracle — Oracle-Free Testing",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #546E7A;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 10px;
    }
    .violation-card {
        background-color: #FFF3E0;
        border-radius: 8px;
        padding: 14px;
        border-left: 5px solid #FF6F00;
        margin-bottom: 12px;
    }
    .pass-card {
        background-color: #E8F5E9;
        border-radius: 8px;
        padding: 14px;
        border-left: 5px solid #2E7D32;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_preset_code(category: str, variant_name: str) -> str:
    """Returns source code of the selected preset."""
    mapping = {
        ("Sorting", "Correct Reference"): sort_list,
        ("Sorting", "Bug: Reverse Input Bias"): sort_list_buggy_reverse,
        ("Sorting", "Bug: Drops Duplicates (set conversion)"): sort_list_buggy_duplicates,
        ("Sorting", "Bug: Off-by-one Boundary Partial Sort"): sort_list_buggy_partial,
        ("Shortest Path", "Correct Reference"): shortest_route,
        ("Shortest Path", "Bug: Asymmetric Directional Bias"): shortest_route_buggy_asymmetric,
        ("Shortest Path", "Bug: Unweighted Hop Count"): shortest_route_buggy_weight,
        ("Duplicate Removal", "Correct Reference"): remove_duplicates,
        ("Duplicate Removal", "Bug: Consecutive-Only Removal"): remove_duplicates_buggy_consecutive,
        ("Duplicate Removal", "Bug: Idempotence Failure (1 drop per run)"): remove_duplicates_buggy_idempotence,
    }
    fn = mapping.get((category, variant_name))
    if fn:
        return inspect.getsource(fn)
    return 'def custom_function(items):\n    """Custom function to test."""\n    return sorted(items)\n'


# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://img.icons8.com/fluency/96/crystal-ball.png", width=64)
st.sidebar.title("🔮 MetaOracle")
st.sidebar.markdown("**Oracle-Free Metamorphic Testing System**")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "Navigation Mode",
    [
        "🔬 Test Runner & Bug Hunter",
        "🧬 Mutation Testing Lab",
        "📊 Comparative Benchmark (Phase 6)",
        "📚 Metamorphic Relations Catalog",
        "📘 Project Viva & Theory Guide",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Target Preset Selection")

category = st.sidebar.selectbox(
    "Function Category",
    ["Sorting", "Shortest Path", "Duplicate Removal", "Custom Python Code"],
    index=0,
)

variant_options = {
    "Sorting": [
        "Bug: Reverse Input Bias",
        "Bug: Drops Duplicates (set conversion)",
        "Bug: Off-by-one Boundary Partial Sort",
        "Correct Reference",
    ],
    "Shortest Path": [
        "Bug: Asymmetric Directional Bias",
        "Bug: Unweighted Hop Count",
        "Correct Reference",
    ],
    "Duplicate Removal": [
        "Bug: Idempotence Failure (1 drop per run)",
        "Bug: Consecutive-Only Removal",
        "Correct Reference",
    ],
    "Custom Python Code": ["User Defined"],
}

chosen_variant = st.sidebar.selectbox("Implementation Variant", variant_options[category], index=0)

test_budget = st.sidebar.select_slider(
    "Number of Generated Tests",
    options=[10, 50, 100, 250, 500, 1000],
    value=50,
)

exec_timeout = st.sidebar.slider("Timeout per test (seconds)", 0.5, 5.0, 2.0, 0.5)

# Session state initialization for test results
if "last_suite_report" not in st.session_state:
    st.session_state.last_suite_report = None
if "last_mutation_report" not in st.session_state:
    st.session_state.last_mutation_report = None


# ==============================================================================
# MODE 1: TEST RUNNER & BUG HUNTER
# ==============================================================================
if app_mode == "🔬 Test Runner & Bug Hunter":
    st.markdown('<div class="main-header">MetaOracle Test Runner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Detect software defects without manual expected-output test cases using Metamorphic Relations.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Code Under Test")
        preset_code = get_preset_code(category, chosen_variant)
        code_input = st.text_area(
            "Python Source Code",
            value=preset_code,
            height=260,
            help="Edit or paste your Python function. Uploaded code will be executed in a safe sandbox.",
        )

        uploaded_file = st.file_uploader("Or upload a .py file", type=["py"])
        if uploaded_file is not None:
            code_input = uploaded_file.read().decode("utf-8")
            st.success("Uploaded file loaded successfully!")

    # AST Suggestion Engine
    suggester = RelationSuggester()
    suggested_relations = suggester.suggest_from_code(code_input)

    with col2:
        st.subheader("2. Metamorphic Relations")
        st.caption("Auto-suggested relations based on AST inspection and function heuristics:")

        all_registered = default_registry.list_all()
        selected_relation_ids = []

        if suggested_relations:
            suggested_ids = {s.relation.relation_id for s in suggested_relations}
            for s in suggested_relations:
                confidence_badge = {
                    "High": "🟢 [High Confidence]",
                    "Medium": "🟡 [Medium Confidence]",
                    "Low": "⚪ [Candidate]",
                }.get(s.confidence, "")

                checked = st.checkbox(
                    f"{confidence_badge} {s.relation.name}",
                    value=True,
                    key=f"chk_{s.relation.relation_id}",
                    help=f"{s.rationale}\nCaveats: {s.domain_caveats}",
                )
                if checked:
                    selected_relation_ids.append(s.relation.relation_id)

            # Option to expand other relations
            with st.expander("Show other available relations from catalog"):
                for rel in all_registered:
                    if rel.relation_id not in suggested_ids:
                        chk = st.checkbox(
                            f"{rel.name} ({rel.category})",
                            value=False,
                            key=f"chk_extra_{rel.relation_id}",
                            help=rel.description,
                        )
                        if chk:
                            selected_relation_ids.append(rel.relation_id)
        else:
            st.info("No specific pattern matched. Select relations manually:")
            for rel in all_registered:
                chk = st.checkbox(
                    f"{rel.name} ({rel.category})",
                    value=(rel.relation_id in ["MR_PERMUTATION_INVARIANCE", "MR_IDEMPOTENCE"]),
                    key=f"chk_manual_{rel.relation_id}",
                )
                if chk:
                    selected_relation_ids.append(rel.relation_id)

    # Execution Action
    st.markdown("---")
    st.subheader("3. Execute Metamorphic Testing")

    input_type = "graph" if "graph" in code_input.lower() or category == "Shortest Path" else "list"

    active_relations = [
        default_registry.get(rid) for rid in selected_relation_ids if default_registry.get(rid) is not None
    ]

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_clicked = st.button("🚀 Run MetaOracle Engine", type="primary", use_container_width=True)

    with col_info:
        st.markdown(
            f"**Configuration**: `{test_budget}` generated test inputs | `{len(active_relations)}` active relations | Input type: `{input_type}`"
        )

    if run_clicked:
        if not active_relations:
            st.error("Please select at least one metamorphic relation to test.")
        else:
            with st.spinner("Generating inputs, applying transformations, and checking relations..."):
                runner = MetamorphicTestRunner(timeout_seconds=exec_timeout, seed=42)
                try:
                    report = runner.run_tests(
                        target_func=code_input,
                        relations=active_relations,
                        test_count=test_budget,
                        input_type=input_type,
                    )
                    st.session_state.last_suite_report = report
                    st.session_state.last_code = code_input
                    st.session_state.last_input_type = input_type
                    st.success("Test suite run completed successfully!")
                except Exception as e:
                    st.error(f"Failed to run test suite: {str(e)}")

    # Display Results
    if st.session_state.last_suite_report is not None:
        rep = st.session_state.last_suite_report
        st.markdown("---")
        st.subheader("4. Test Execution Results & Metrics")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Inputs Tested", f"{test_budget}")
        m2.metric("Total Tests Run", f"{rep.total_tests}")
        m3.metric("Passed Tests", f"{rep.passed_tests}")
        m4.metric(
            "Violations Found",
            f"{rep.violated_tests}",
            delta=f"-{rep.violated_tests}" if rep.violated_tests > 0 else "0",
            delta_color="inverse",
        )
        m5.metric("Pass Rate", f"{rep.pass_rate:.1f}%")

        if rep.has_violations:
            st.error(
                f"🚨 **Defect Detected**: {rep.violated_tests} test violations were discovered without knowing any expected output!"
            )
        else:
            st.success("✅ **All Relations Satisfied**: No metamorphic violations were observed under the tested input budget.")

        # Relation Breakdown Table
        st.markdown("#### Metamorphic Relation Breakdown")
        table_rows = []
        for r_id, r_rep in rep.relation_reports.items():
            status = "🔴 VIOLATED" if r_rep.violated_tests > 0 else "🟢 PASSED"
            table_rows.append(
                {
                    "Relation Name": r_rep.relation_name,
                    "Status": status,
                    "Passed": r_rep.passed_tests,
                    "Violations": r_rep.violated_tests,
                    "Pass Rate": f"{r_rep.pass_rate}%",
                    "Duration (ms)": round(r_rep.total_duration_ms, 2),
                }
            )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

        # Counterexample Inspector
        if rep.all_counterexamples:
            st.markdown("#### 🔍 Failing Counterexamples (Reproducible Bug Pairs)")
            st.caption("Each counterexample illustrates source vs follow-up inputs where the metamorphic relation broke.")

            for i, ce in enumerate(rep.all_counterexamples[:6], start=1):
                with st.expander(f"Counterexample #{i}: [{ce.relation_name}] — Click to inspect"):
                    c_left, c_right = st.columns(2)
                    with c_left:
                        st.markdown("**Source Input ($x$):**")
                        st.code(str(ce.source_input))
                        st.markdown("**Source Output ($f(x)$):**")
                        st.code(str(ce.source_output))
                    with c_right:
                        st.markdown("**Follow-up Input ($x'$):**")
                        st.code(str(ce.follow_up_input))
                        st.markdown("**Follow-up Output ($f(x')$):**")
                        st.code(str(ce.follow_up_output))

                    st.warning(f"**Violation Diagnostic:** {ce.violation_message}")
                    if ce.expected_relation:
                        st.markdown(f"**Expected Rule:** `{ce.expected_relation}` | **Observed:** `{ce.actual_observation}`")

        # Export Report Section
        st.markdown("#### 💾 Export Test Reports")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            json_str = json.dumps(rep.to_dict(), indent=2)
            st.download_button(
                label="📥 Download Full Report (JSON)",
                data=json_str,
                file_name=f"metaoracle_report_{category.lower().replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_dl2:
            ce_rows = [ce.to_dict() for ce in rep.all_counterexamples]
            if ce_rows:
                csv_data = pd.DataFrame(ce_rows).to_csv(index=False)
            else:
                csv_data = pd.DataFrame(table_rows).to_csv(index=False)
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv_data,
                file_name=f"metaoracle_counterexamples_{category.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ==============================================================================
# MODE 2: MUTATION TESTING LAB
# ==============================================================================
elif app_mode == "🧬 Mutation Testing Lab":
    st.markdown('<div class="main-header">Mutation Testing Lab (Phase 4)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Evaluate the quality and fault-detection capability of metamorphic tests by injecting artificial bugs.</div>',
        unsafe_allow_html=True,
    )

    code_to_mutate = (
        st.session_state.get("last_code")
        or get_preset_code(category, chosen_variant)
    )

    st.subheader("1. Active Program for Mutation Analysis")
    st.code(code_to_mutate, language="python")

    c1, c2 = st.columns([1, 1])
    with c1:
        max_mutants = st.slider("Maximum mutants to generate", 5, 25, 12)
    with c2:
        st.write("")
        st.write("")
        run_mut_btn = st.button("🧬 Run Mutation Analysis", type="primary", use_container_width=True)

    if run_mut_btn:
        with st.spinner("Synthesizing AST mutants and evaluating metamorphic test suite..."):
            tester = MutationTester(exec_timeout, seed=42)
            input_type = "graph" if "graph" in code_to_mutate.lower() or category == "Shortest Path" else "list"

            # Auto suggest relations if none cached
            suggester = RelationSuggester()
            sugg = suggester.suggest_from_code(code_to_mutate)
            active_rels = [s.relation for s in sugg] or default_registry.list_all()

            mut_report = tester.run_mutation_analysis(
                source_code=code_to_mutate,
                relations=active_rels,
                test_count=min(test_budget, 40),
                max_mutants=max_mutants,
                input_type=input_type,
            )
            st.session_state.last_mutation_report = mut_report
            st.success("Mutation testing completed!")

    if st.session_state.last_mutation_report is not None:
        mrep = st.session_state.last_mutation_report
        st.markdown("---")
        st.subheader("2. Mutation Analysis Metrics")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Mutants", f"{mrep.total_mutants}")
        m2.metric("Killed Mutants", f"{mrep.killed_mutants}")
        m3.metric("Survived Mutants", f"{mrep.survived_mutants}")
        m4.metric("Mutation Score", f"{mrep.mutation_score:.1f}%")

        st.latex(r"\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Evaluated Mutants}} \times 100")

        # Relation Kill Breakdown
        if mrep.relation_kill_breakdown:
            st.markdown("#### 🎯 Mutant Kill Breakdown by Metamorphic Relation")
            k_df = pd.DataFrame(
                [
                    {"Metamorphic Relation": k, "Mutants Killed": v}
                    for k, v in mrep.relation_kill_breakdown.items()
                ]
            )
            st.dataframe(k_df, use_container_width=True)

        # Mutants List and Diff Inspector
        st.markdown("#### 🔬 Injected Mutants & Code Diffs")
        for res in mrep.results:
            status_badge = "🟢 KILLED" if res.status == "KILLED" else "🔴 SURVIVED"
            with st.expander(f"{res.mutant.mutant_id}: {status_badge} — {res.mutant.description}"):
                st.markdown(f"**Operator:** `{res.mutant.operator_name}` at Line `{res.mutant.line_number}`")
                if res.status == "KILLED":
                    st.success(f"**Killed By Relation:** {res.killing_relation_name}")
                    if res.violation_message:
                        st.caption(f"Reason: {res.violation_message}")
                else:
                    st.warning("⚠️ Mutant Survived: Metamorphic tests did not distinguish this mutant from original code.")

                st.markdown("**Unified Diff:**")
                st.code(res.mutant.diff, language="diff")

        # Export Mutation Report Section
        st.markdown("#### 💾 Export Mutation Report")
        m_json_str = json.dumps(mrep.to_dict(), indent=2)
        st.download_button(
            label="📥 Download Mutation Report (JSON)",
            data=m_json_str,
            file_name=f"metaoracle_mutation_report_{mrep.target_function_name}.json",
            mime="application/json",
            use_container_width=True,
        )


# ==============================================================================
# MODE 3: COMPARATIVE BENCHMARK (PHASE 6)
# ==============================================================================
elif app_mode == "📊 Comparative Benchmark (Phase 6)":
    st.markdown('<div class="main-header">Phase 6: Comparative Empirical Evaluation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Head-to-head benchmark comparing MetaOracle against Random Testing and Handcrafted Unit Tests.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        In this evaluation, three distinct testing paradigms are executed against identical seeded bug variants:
        1. **Random Testing (Crash-Only Oracle)**: Only flags errors if an unhandled crash/exception occurs.
        2. **Expected-Output Unit Testing**: Uses conventional handcrafted input/output assertions.
        3. **MetaOracle (Metamorphic Testing)**: Oracle-free automated input generation and relation verification.
        """
    )

    if st.button("📊 Run Comparative Benchmark", type="primary"):
        with st.spinner("Benchmarking testing approaches across all seeded bug variants..."):
            comparator = BenchmarkComparator(test_budget=test_budget, seed=42)
            results = comparator.run_full_comparison()
            st.session_state.bench_results = results
            st.success("Benchmark completed!")

    if "bench_results" in st.session_state:
        results = st.session_state.bench_results
        st.markdown("---")
        st.subheader("Benchmark Results Matrix")

        df_bench = pd.DataFrame([r.to_dict() for r in results])
        st.dataframe(
            df_bench[
                [
                    "technique_name",
                    "oracle_type",
                    "detection_rate",
                    "detected_bugs_count",
                    "total_evaluated_bugs",
                    "duration_ms",
                    "oracle_effort",
                ]
            ],
            use_container_width=True,
        )

        st.markdown("#### Fault Detection Comparison")
        chart_data = pd.DataFrame(
            {
                "Technique": [r.technique_name for r in results],
                "Detection Rate (%)": [r.detection_rate for r in results],
            }
        ).set_index("Technique")
        st.bar_chart(chart_data)

        st.markdown("#### Detailed Technique Breakdown")
        for r in results:
            with st.expander(f"📌 {r.technique_name} — Detection: {r.detection_rate:.1f}%"):
                st.markdown(f"**Oracle Mechanism:** {r.oracle_type}")
                st.markdown(f"**Manual Effort:** {r.oracle_effort}")
                st.markdown(f"**Bugs Caught ({r.detected_bugs_count}/{r.total_evaluated_bugs}):** {', '.join(r.detected_bug_names) or 'None'}")
                if r.missed_bug_names:
                    st.markdown(f"**Missed Bugs:** {', '.join(r.missed_bug_names)}")
                st.info(f"**Key Finding:** {r.notes}")


# ==============================================================================
# MODE 4: METAMORPHIC RELATIONS CATALOG
# ==============================================================================
elif app_mode == "📚 Metamorphic Relations Catalog":
    st.markdown('<div class="main-header">Catalog of Metamorphic Relations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Comprehensive library of formal relations, mathematical formulations, and domain requirements.</div>',
        unsafe_allow_html=True,
    )

    rels = default_registry.list_all()

    for r in rels:
        with st.expander(f"🔹 {r.name} [{r.category}] ({r.relation_id})"):
            st.markdown(f"**Description:** {r.description}")
            st.markdown(f"**Domain Requirements:** `{r.domain_requirements}`")
            st.markdown(f"**Output Derived Transformation:** `{'Yes (f(f(x)))' if r.is_output_derived else 'No (x -> x\')'}`")


# ==============================================================================
# MODE 5: VIVA & THEORY GUIDE
# ==============================================================================
elif app_mode == "📘 Project Viva & Theory Guide":
    st.markdown('<div class="main-header">Viva Voce & Technical Defense Guide</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Key concepts, academic justification, and examiner questions for MetaOracle.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 1. What is the Test Oracle Problem?
        A test oracle is any mechanism that determines whether the output of a program is correct for a given input. In complex real-world software (machine learning, simulations, pathfinding, search engines, compilers), the correct expected output is often unknown or prohibitive to compute manually.

        ### 2. How does Metamorphic Testing solve this?
        Instead of asserting the correctness of an isolated output:
        $$\text{Output}(x) = y_{\text{expected}}$$
        Metamorphic Testing (MT) checks the relationship between multiple executions:
        $$R(x, x', f(x), f(x'))$$
        If this metamorphic relation is violated, a software fault or invalid specification assumption is detected **without needing an oracle**.

        ### 3. Crucial Domain Caveats (Examiner Defense)
        - Relations must only be applied to their intended domain (e.g. graph symmetry applies strictly to undirected graphs with symmetric weights).
        - A relation violation indicates a bug or invalid relation assumption; it does not prove the program is correct when it passes (soundness vs completeness).
        - Static AST analysis assists developer selection, but human review remains valuable.

        ### 4. Mutation Score Interpretation
        $$\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Evaluated Mutants}} \times 100$$
        High mutation scores validate that our metamorphic relations are sensitive to subtle syntactic and logical defects.
        """
    )

# Footer
st.markdown("---")
st.caption("MetaOracle Prototype | Built with Python, Streamlit, and Hypothesis | Oracle-Free Metamorphic Testing")
