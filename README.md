# 🔮 MetaOracle: Oracle-Free Testing Using Metamorphic Relations

> **A Python-based Metamorphic Testing Studio & Automation Framework**  
> Detect software bugs without manually writing expected outputs for every test case.

---

## 📌 Executive Summary & Problem Statement

In software testing, the **Test Oracle Problem** refers to the difficulty or practical impossibility of verifying whether the output produced by a program is correct. For numerous domains—including machine learning models, search algorithms, scientific simulations, graphics rendering, and graph optimizations—an automated oracle does not exist, and manual calculation of expected outputs is cost-prohibitive.

**MetaOracle** solves this challenge by leveraging **Metamorphic Testing (MT)**. Instead of asserting absolute input-output correctness:
$$\text{Output}(x) \stackrel{?}{=} y_{\text{expected}}$$
MetaOracle checks whether multiple executions satisfy essential domain properties known as **Metamorphic Relations (MR)**:
$$R\big(x,\, x',\, f(x),\, f(x')\big) = \text{True}$$

A violation of an established metamorphic relation indicates an implementation defect without needing to know the ground-truth output.

---

## 🚀 Key Deliverables & System Architecture

```text
backend/
├── app/
│   ├── api/                 # REST Routers (tests, relations, mutations, benchmarks, snippets, stats)
│   ├── database/            # SQLAlchemy Engine, SQLite models (TestRun, TestCase, MutationRun, etc.)
│   ├── schemas/             # Pydantic request & response validation models
│   ├── services/            # TestRunner, MutationTester, Suggester & Benchmark bridge services
│   ├── config.py            # App settings, DB path, CORS settings
│   └── main.py              # FastAPI application entry point
frontend/
├── index.html               # Modern Single Page Application (SPA) with Tailwind CSS
├── css/styles.css           # Glassmorphism theme, diff formatting & micro-animations
└── js/
    ├── api.js               # REST API client with error handling
    ├── app.js               # Reactive UI controller, state management & tab router
    └── charts.js            # Chart.js visualizations (pass/fail trends, mutation scores, benchmarks)
metaoracle/
├── engine/                  # Core Metamorphic test generation, safe sandbox execution, and checking
├── relations/               # Metamorphic Relations Catalog (10 reusable formal relations)
├── suggestion/              # AST static analysis & heuristic relation recommender
├── mutation/                # AST mutant synthesis and mutation score evaluation
├── sample_programs/         # Correct implementations & seeded bug variants
└── evaluation/              # Empirical comparison against Random & Unit testing
tests/                       # Pytest test suite (35 automated tests covering DB, API & Engine)
run_server.py                # One-click Server launcher (FastAPI + SQLite + Frontend SPA)
start.bat / start.sh         # Windows and Unix one-click startup scripts
requirements.txt             # Project dependencies
```

---

## 🔬 Supported Sample Programs & Seeded Bug Variants

| Function | Reference Implementation | Seeded Bug Variants | Violated Metamorphic Relations |
| :--- | :--- | :--- | :--- |
| `sort_list()` | Timsort/Quicksort | 1. **Reverse Input Bias** (`arr[0] > arr[-1]` sorts descending)<br>2. **Drops Duplicates** (converts to `set`)<br>3. **Partial Sort** (off-by-one boundary loop) | • Permutation Invariance<br>• Reverse Invariance<br>• Size Conservation (`len(f(x)) == len(x)`) |
| `shortest_route()` | Dijkstra on undirected graphs | 1. **Asymmetric Traversal** (directional alphabetical bias)<br>2. **Unweighted Hop Count** (ignores edge weights) | • Graph Undirected Symmetry<br>$\text{dist}(A, B) == \text{dist}(B, A)$ |
| `remove_duplicates()` | Order-preserving unique set | 1. **Consecutive-Only** (Unix `uniq` style)<br>2. **Idempotence Failure** (drops at most 1 duplicate per run) | • Idempotence $f(f(x)) == f(x)$<br>• Unique Completeness<br>• Duplicate Amplification |

---

## 📚 Catalog of Metamorphic Relations (MR Library)

1. **Reverse-Input Invariance (`MR_REVERSE_INVARIANCE`)**: $f(\text{rev}(x)) == f(x)$
2. **Permutation Invariance (`MR_PERMUTATION_INVARIANCE`)**: $f(\text{permute}(x)) == f(x)$
3. **Idempotence Property (`MR_IDEMPOTENCE`)**: $f(f(x)) == f(x)$
4. **Graph Undirected Symmetry (`MR_GRAPH_SYMMETRY`)**: $\text{dist}(G, u, v) == \text{dist}(G, v, u)$
5. **Scaling Proportionality (`MR_SCALING_PROPORTIONALITY`)**: $f(k \cdot x) == k \cdot f(x)$
6. **Additive Shift Equivariance (`MR_ADDITIVE_SHIFT`)**: $f(x + c) == f(x) + c$
7. **Duplicate Amplification Invariance (`MR_DUPLICATE_AMPLIFICATION`)**: $f(\text{amplify}(x)) == f(x)$
8. **Subset Monotonicity (`MR_SUBSET_MONOTONICITY`)**: $\text{len}(f(x \cup \{y\})) \ge \text{len}(f(x))$
9. **Size Conservation (`MR_SIZE_CONSERVATION`)**: $\text{len}(f(x)) == \text{len}(x)$
10. **Unique Completeness (`MR_UNIQUE_COMPLETENESS`)**: $\text{len}(f(x)) == \text{len}(\text{set}(f(x)))$

---

## 🧬 Mutation Testing Analysis

Mutation testing measures whether metamorphic tests can distinguish real programs from intentionally injected artificial defects.
$$\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Non-Equivalent Mutants}} \times 100\%$$

MetaOracle implements standard AST mutation operators:
- **ROR (Relational Operator Replacement)**: `>` $\to$ `<`, `==` $\to$ `!=`, `>=` $\to$ `<=`
- **AOR (Arithmetic Operator Replacement)**: `+` $\to$ `-`, `-` $\to$ `+`, `*` $\to$ `//`
- **LCR (Logical Connector Replacement)**: `and` $\to$ `or`, `or` $\to$ `and`
- **COR (Constant Inversion)**: `True` $\to$ `False`, `0` $\to$ `1`

---

## 📊 Phase 6: Comparative Empirical Benchmark

MetaOracle was evaluated against two baseline testing strategies across all seeded bug variants:

| Testing Paradigm | Oracle Type | Manual Oracle Effort | Bug Detection Rate | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **Random Testing** | Crash-Only Oracle | **Zero** | **0.0%** | Fails on silent logic bugs that do not raise unhandled exceptions. |
| **Expected-Output Unit Testing** | Handcrafted Assertions | **High** (Labor-intensive) | **42.9%** | Limited strictly to the few scenarios the tester manually computed. |
| **MetaOracle (Our Approach)** | Oracle-Free Metamorphic Relations | **Low** (Define relations once) | **85.7%** | Automatically exposes subtle semantic bugs and counterexample pairs. |

---

## 💻 Quick Start & Usage Guide

### 1. Installation
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Launch the Full-Stack Platform (FastAPI + SQLite + Modern SPA)
Run the unified server launcher:
```powershell
python run_server.py
# Or double-click start.bat (Windows) / ./start.sh (Linux/macOS)
```
Open your browser at:
- **Web Studio (Frontend SPA)**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Database Schema**: Persistent SQLite database stored at `./metaoracle.db`

### 3. Launch the Streamlit Dashboard (Alternative)
```powershell
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run the Automated 6-Step Demonstration Script
```powershell
python demonstration.py
```

### 5. Run the CLI Runner
```powershell
# Test buggy reverse sorting
python -m metaoracle.cli --function sort_list --variant buggy_reverse --tests 50 --mutation

# Run Phase 6 comparative evaluation
python -m metaoracle.cli --evaluate --tests 50
```

### 6. Run the Automated Pytest Suite
```powershell
pytest -v
```

---

## 🎓 Viva Voce & Academic Defense Questions

1. **Why is a relation violation not an absolute mathematical proof of a bug?**  
   *Answer*: A metamorphic relation violation proves that $(x, x', f(x), f(x'))$ does not satisfy the specified relation. This can occur either because the program has a bug or because the user selected an invalid relation assumption that does not hold for the function's input domain.

2. **Why can't static AST analysis find all metamorphic relations automatically?**  
   *Answer*: Determining semantic correctness and universal invariants of arbitrary code is undecidable (Rice's Theorem). MetaOracle uses static heuristics and AST pattern matching to suggest candidate relations, which the developer reviews and confirms.

3. **What domain restrictions must be respected?**  
   *Answer*: Undirected graph symmetry applies exclusively to graphs where edge costs are symmetric. If applied to a directed graph (like a one-way street network), asymmetric outputs are expected and do not constitute a bug.
