"""
Pydantic Schemas for request validation and response serialization.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Metamorphic Testing Schemas ---

class RunTestRequest(BaseModel):
    category: str = Field(..., description="Function category: Sorting, Shortest Path, Duplicate Removal, Custom Python Code")
    variant: str = Field(..., description="Target variant name or 'Custom'")
    custom_code: Optional[str] = Field(None, description="Custom Python source code to execute")
    input_type: Optional[str] = Field("list", description="Input type generator: list, graph, int_list, etc.")
    selected_relation_ids: List[str] = Field(default_factory=list, description="IDs of relations to evaluate")
    test_budget: int = Field(50, ge=1, le=1000, description="Number of source test inputs to generate")
    seed: Optional[int] = Field(42, description="Random seed for reproducible input generation")


class TestCaseResultSchema(BaseModel):
    test_id: int
    relation_id: str
    relation_name: str
    source_input: str
    follow_up_input: str
    source_output: str
    follow_up_output: str
    passed: bool
    is_violation: bool
    is_error: bool
    error_message: Optional[str] = None
    violation_message: Optional[str] = None
    expected_relation: str = ""
    actual_observation: str = ""
    duration_ms: float = 0.0


class RelationReportSchema(BaseModel):
    relation_id: str
    relation_name: str
    total_tests: int
    passed_tests: int
    violated_tests: int
    error_tests: int
    pass_rate: float
    total_duration_ms: float
    counterexamples_count: int
    counterexamples: List[TestCaseResultSchema] = []


class TestRunResponse(BaseModel):
    id: int
    created_at: Optional[str] = None
    function_name: str
    category: str
    variant: str
    input_type: str
    test_budget: int
    total_tests: int
    passed_tests: int
    violated_tests: int
    error_tests: int
    pass_rate: float
    duration_ms: float
    status: str
    relation_summary: Dict[str, Any] = {}
    counterexamples_count: int
    source_code: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None


# --- Suggestion Schemas ---

class SuggestRequest(BaseModel):
    category: Optional[str] = None
    variant: Optional[str] = None
    code: Optional[str] = None


class SuggestionItem(BaseModel):
    relation_id: str
    relation_name: str
    category: str
    confidence: str  # HIGH, MEDIUM, LOW
    rationale: str
    formula: str


class SuggestResponse(BaseModel):
    function_name: str
    suggestions: List[SuggestionItem]


# --- Mutation Schemas ---

class RunMutationRequest(BaseModel):
    category: str
    variant: str
    custom_code: Optional[str] = None
    test_budget: int = Field(30, ge=5, le=200)
    selected_relation_ids: Optional[List[str]] = None


class MutantItem(BaseModel):
    mutant_id: str
    operator: str
    description: str
    line_number: int
    status: str  # KILLED, SURVIVED, ERROR
    killing_relation_id: Optional[str] = None
    killing_relation_name: Optional[str] = None
    violation_message: Optional[str] = None
    failing_input: Optional[str] = None
    diff: str


class MutationRunResponse(BaseModel):
    id: int
    created_at: Optional[str] = None
    function_name: str
    category: str
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    error_mutants: int
    mutation_score: float
    duration_ms: float
    mutants: List[MutantItem]


# --- Benchmark Schemas ---

class RunBenchmarkRequest(BaseModel):
    budget: int = Field(50, ge=10, le=500)


class BenchmarkTechniqueResult(BaseModel):
    technique_name: str
    oracle_type: str
    oracle_effort: str
    tests_executed: int
    duration_ms: float
    detected_bugs_count: int
    total_evaluated_bugs: int
    detection_rate: float
    detected_bug_names: List[str]
    missed_bug_names: List[str]
    notes: str


class BenchmarkRunResponse(BaseModel):
    id: int
    created_at: Optional[str] = None
    test_budget: int
    total_scenarios: int
    results: List[BenchmarkTechniqueResult]
    summary_notes: Optional[str] = None


# --- Relations Catalog & Custom Relations ---

class RelationDetail(BaseModel):
    relation_id: str
    name: str
    description: str
    category: str
    formula: str
    is_custom: bool = False


class CreateCustomRelationRequest(BaseModel):
    relation_id: str
    name: str
    description: str
    category: str = "Custom"
    formula: str


# --- Code Snippet Schemas ---

class SnippetCreateRequest(BaseModel):
    title: str
    category: str = "Custom"
    code: str
    input_type: str = "list"


class SnippetResponse(BaseModel):
    id: int
    title: str
    category: str
    code: str
    input_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Dashboard Stats Schemas ---

class DashboardStatsResponse(BaseModel):
    total_runs: int
    total_tests_executed: int
    total_violations_detected: int
    overall_pass_rate: float
    recent_runs: List[Dict[str, Any]]
    total_mutations_run: int
    avg_mutation_score: float
    total_custom_relations: int
    total_snippets: int
