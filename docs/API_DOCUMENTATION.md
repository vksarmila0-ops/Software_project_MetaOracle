# 🔮 MetaOracle REST API & Database Documentation

## 🌐 Overview
The MetaOracle Full-Stack system features a decoupled, high-performance REST API built with **FastAPI** and **SQLAlchemy ORM**, backed by a persistent **SQLite** database (`metaoracle.db`).

---

## 🗄️ Database Architecture (`metaoracle.db`)

### 1. `test_runs`
Stores historical metamorphic test executions.
- `id` (INTEGER, PK, Auto-increment)
- `created_at` (DATETIME, UTC timestamp)
- `function_name` (VARCHAR)
- `category` (VARCHAR, e.g. Sorting, Shortest Path, Duplicate Removal, Custom)
- `variant` (VARCHAR, e.g. Bug: Reverse Input Bias)
- `input_type` (VARCHAR, 'list' | 'graph')
- `test_budget` (INTEGER, number of source inputs)
- `total_tests` (INTEGER, total tests across all relations)
- `passed_tests` (INTEGER)
- `violated_tests` (INTEGER)
- `error_tests` (INTEGER)
- `pass_rate` (FLOAT, percentage)
- `duration_ms` (FLOAT)
- `status` (VARCHAR: `PASSED`, `VIOLATED`, `ERROR`)
- `relation_summary` (TEXT, serialized JSON breakdown per relation)
- `counterexamples_count` (INTEGER)
- `source_code` (TEXT, tested source code)

### 2. `test_cases`
Stores individual test case executions, inputs, outputs, and counterexamples.
- `id` (INTEGER, PK)
- `test_run_id` (INTEGER, FK -> `test_runs.id`, CASCADE delete)
- `test_index` (INTEGER)
- `relation_id` (VARCHAR, e.g. `MR_REVERSE_INVARIANCE`)
- `relation_name` (VARCHAR)
- `source_input` (TEXT)
- `follow_up_input` (TEXT)
- `source_output` (TEXT)
- `follow_up_output` (TEXT)
- `passed` (BOOLEAN)
- `is_violation` (BOOLEAN)
- `is_error` (BOOLEAN)
- `error_message` (TEXT)
- `violation_message` (TEXT)
- `expected_relation` (TEXT)
- `actual_observation` (TEXT)
- `duration_ms` (FLOAT)

### 3. `mutation_runs`
Stores AST mutation analysis records.
- `id` (INTEGER, PK)
- `created_at` (DATETIME)
- `function_name` (VARCHAR)
- `category` (VARCHAR)
- `total_mutants` (INTEGER)
- `killed_mutants` (INTEGER)
- `survived_mutants` (INTEGER)
- `error_mutants` (INTEGER)
- `mutation_score` (FLOAT, percentage)
- `duration_ms` (FLOAT)
- `results_json` (TEXT, detailed mutant diffs, killing relation)

### 4. `benchmark_runs`
Stores Phase 6 comparative evaluation runs.
- `id` (INTEGER, PK)
- `created_at` (DATETIME)
- `test_budget` (INTEGER)
- `total_scenarios` (INTEGER, default 7)
- `results_json` (TEXT, comparisons across Random, Unit, Metamorphic testing)
- `summary_notes` (TEXT)

### 5. `custom_relations`
Stores user-defined metamorphic relations.
- `id` (INTEGER, PK)
- `relation_id` (VARCHAR, UNIQUE)
- `name` (VARCHAR)
- `description` (TEXT)
- `category` (VARCHAR)
- `formula` (VARCHAR)
- `created_at` (DATETIME)

### 6. `code_snippets`
Stores custom Python algorithm snippets.
- `id` (INTEGER, PK)
- `title` (VARCHAR)
- `category` (VARCHAR)
- `code` (TEXT)
- `input_type` (VARCHAR)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

---

## 🚀 REST API Endpoints Reference

### Metamorphic Testing
- `POST /api/tests/run`: Run metamorphic tests on preset or custom code, persisting run and counterexamples.
- `GET /api/tests/history`: Get paginated test run history with filtering (`category`, `status`, `limit`, `offset`).
- `GET /api/tests/presets`: Get list of supported algorithm presets and bug variants.
- `GET /api/tests/{run_id}`: Retrieve detailed test run with all counterexamples.
- `DELETE /api/tests/{run_id}`: Delete a test run and its associated test cases.

### Metamorphic Relations & AST Suggestions
- `GET /api/relations`: List all built-in and user-defined relations.
- `GET /api/relations/{relation_id}`: Retrieve details for a specific relation.
- `POST /api/relations/custom`: Save a new custom relation to the database.
- `POST /api/relations/suggest`: Analyze code AST to auto-recommend relations with confidence ratings.

### AST Mutation Testing
- `POST /api/mutation/run`: Synthesize mutants (ROR, AOR, LCR, COR) and evaluate mutation score.
- `GET /api/mutation/history`: Get previous mutation testing runs.
- `GET /api/mutation/{run_id}`: Inspect a specific mutation run and code diffs.

### Phase 6 Comparative Benchmark Arena
- `POST /api/benchmark/run`: Execute empirical comparison across Random, Unit, and Metamorphic testing.
- `GET /api/benchmark/history`: Get previous benchmark runs.
- `GET /api/benchmark/{run_id}`: Inspect specific benchmark run.

### Code Snippets
- `GET /api/snippets`: List saved code snippets.
- `POST /api/snippets`: Create a new snippet.
- `GET /api/snippets/{id}`: Get a snippet.
- `DELETE /api/snippets/{id}`: Delete a snippet.

### System & Dashboard Stats
- `GET /api/health`: Service health check and database connectivity.
- `GET /api/stats/dashboard`: Real-time aggregated KPIs and recent activity.
