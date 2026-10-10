"""
Relation Suggester: Analyzes function signatures, names, docstrings, and AST structure
to recommend suitable metamorphic relations.
"""

import ast
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union
from ..relations.base import MetamorphicRelation
from ..relations.registry import default_registry


@dataclass
class SuggestedRelation:
    """A metamorphic relation suggested by static heuristics and AST inspection."""
    relation: MetamorphicRelation
    confidence: str  # "High", "Medium", "Low"
    rationale: str
    domain_caveats: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation.relation_id,
            "name": self.relation.name,
            "category": self.relation.category,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "domain_caveats": self.domain_caveats,
            "description": self.relation.description,
        }


class RelationSuggester:
    """
    Rule-based metamorphic relation recommender using AST analysis,
    parameter heuristics, docstring inspection, and function names.
    
    Note: As per software testing theory, static analysis cannot guarantee validity
    for arbitrary code; suggestions are presented for developer review.
    """

    def __init__(self, registry=None):
        self.registry = registry or default_registry

    def suggest_from_callable(self, func: Callable) -> List[SuggestedRelation]:
        """Suggests relations by inspecting a live callable object."""
        import inspect
        try:
            source = inspect.getsource(func)
            return self.suggest_from_code(source, func.__name__)
        except Exception:
            # Fallback to name and signature inspection
            name = getattr(func, "__name__", "")
            doc = inspect.getdoc(func) or ""
            return self._infer_suggestions(name, doc, [], set())

    def suggest_from_code(self, code_str: str, target_fn_name: Optional[str] = None) -> List[SuggestedRelation]:
        """
        Parses source code into an AST and derives metamorphic relation recommendations.
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError:
            return []

        fn_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if not fn_nodes:
            return []

        # Target selected or last defined function
        selected_fn = fn_nodes[-1]
        if target_fn_name:
            for fn in fn_nodes:
                if fn.name == target_fn_name:
                    selected_fn = fn
                    break

        fn_name = selected_fn.name.lower()
        docstring = ast.get_docstring(selected_fn) or ""
        params = [arg.arg.lower() for arg in selected_fn.args.args]
        
        # Collect AST indicators
        ast_ops = set()
        for sub in ast.walk(selected_fn):
            if isinstance(sub, ast.Compare):
                ast_ops.add("comparison")
            elif isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name):
                    ast_ops.add(sub.func.id.lower())
                elif isinstance(sub.func, ast.Attribute):
                    ast_ops.add(sub.func.attr.lower())
            elif isinstance(sub, (ast.For, ast.While)):
                ast_ops.add("loop")

        return self._infer_suggestions(fn_name, docstring.lower(), params, ast_ops)

    def _infer_suggestions(
        self,
        name: str,
        doc: str,
        params: List[str],
        ast_ops: set,
    ) -> List[SuggestedRelation]:
        """Applies rule-based heuristic matching against known metamorphic patterns."""
        suggestions: List[SuggestedRelation] = []

        is_sorting = any(k in name for k in ["sort", "order", "rank"]) or "sorted" in ast_ops
        is_graph = any(k in name for k in ["route", "path", "graph", "dijkstra", "distance", "shortest"]) or \
                   any(p in params for p in ["graph", "start", "end", "src", "dst", "u", "v"])
        is_dedup = any(k in name for k in ["dup", "unique", "distinct", "dedup", "clean", "filter"]) or \
                   "set" in ast_ops

        # Pattern 1: Sorting Functions
        if is_sorting:
            r_perm = self.registry.get("MR_PERMUTATION_INVARIANCE")
            if r_perm:
                suggestions.append(SuggestedRelation(
                    relation=r_perm,
                    confidence="High",
                    rationale="Sorting outputs should be invariant to any permutation/reordering of the input list.",
                    domain_caveats="Applies to comparable items. Stability considerations apply if keys are duplicated.",
                ))

            r_rev = self.registry.get("MR_REVERSE_INVARIANCE")
            if r_rev:
                suggestions.append(SuggestedRelation(
                    relation=r_rev,
                    confidence="High",
                    rationale="Reversing input sequence should produce identical sorted order: sort(rev(x)) == sort(x).",
                    domain_caveats="Requires deterministic comparison.",
                ))

            r_idem = self.registry.get("MR_IDEMPOTENCE")
            if r_idem:
                suggestions.append(SuggestedRelation(
                    relation=r_idem,
                    confidence="High",
                    rationale="Sorting an already sorted sequence is idempotent: sort(sort(x)) == sort(x).",
                    domain_caveats="Input and output types must be compatible collections.",
                ))

            r_scale = self.registry.get("MR_SCALING_PROPORTIONALITY")
            if r_scale:
                suggestions.append(SuggestedRelation(
                    relation=r_scale,
                    confidence="Medium",
                    rationale="For numeric lists, positive scalar scaling preserves order: sort(k * x) == k * sort(x).",
                    domain_caveats="Requires numeric elements and positive multiplier k > 0.",
                ))

            r_shift = self.registry.get("MR_ADDITIVE_SHIFT")
            if r_shift:
                suggestions.append(SuggestedRelation(
                    relation=r_shift,
                    confidence="Medium",
                    rationale="Adding a constant offset preserves the ordering structure: sort(x + c) == sort(x) + c.",
                    domain_caveats="Requires numeric elements (int or float).",
                ))

            r_subset = self.registry.get("MR_SUBSET_MONOTONICITY")
            if r_subset:
                suggestions.append(SuggestedRelation(
                    relation=r_subset,
                    confidence="Medium",
                    rationale="Appending an element cannot decrease the length of a complete sorted output.",
                    domain_caveats="Assumes no filtering of inputs.",
                ))

            r_size = self.registry.get("MR_SIZE_CONSERVATION")
            if r_size:
                suggestions.append(SuggestedRelation(
                    relation=r_size,
                    confidence="High",
                    rationale="Sorting must strictly conserve the number of elements: len(f(x)) == len(x).",
                    domain_caveats="Fails if sorting drops duplicates or truncates inputs.",
                ))

        # Pattern 2: Graph Routing & Distance
        elif is_graph:
            r_sym = self.registry.get("MR_GRAPH_SYMMETRY")
            if r_sym:
                suggestions.append(SuggestedRelation(
                    relation=r_sym,
                    confidence="High",
                    rationale="In undirected networks with symmetric edge weights, dist(A, B) must equal dist(B, A).",
                    domain_caveats="Crucial: only valid for undirected graphs. Directed graphs will violate this.",
                ))

        # Pattern 3: Deduplication & Set Reductions
        elif is_dedup:
            r_idem = self.registry.get("MR_IDEMPOTENCE")
            if r_idem:
                suggestions.append(SuggestedRelation(
                    relation=r_idem,
                    confidence="High",
                    rationale="Deduplication is inherently idempotent: dedup(dedup(x)) == dedup(x).",
                    domain_caveats="Applies to idempotent clean/normalize pipelines.",
                ))

            r_uniq = self.registry.get("MR_UNIQUE_COMPLETENESS")
            if r_uniq:
                suggestions.append(SuggestedRelation(
                    relation=r_uniq,
                    confidence="High",
                    rationale="Deduplicated output must contain strictly zero duplicates: len(f(x)) == len(set(f(x))).",
                    domain_caveats="Catches flawed consecutive-only duplicate removers.",
                ))

            r_amp = self.registry.get("MR_DUPLICATE_AMPLIFICATION")
            if r_amp:
                suggestions.append(SuggestedRelation(
                    relation=r_amp,
                    confidence="High",
                    rationale="Adding redundant duplicate occurrences of elements should not alter the unique output.",
                    domain_caveats="Requires deduplication semantics.",
                ))

            r_subset = self.registry.get("MR_SUBSET_MONOTONICITY")
            if r_subset:
                suggestions.append(SuggestedRelation(
                    relation=r_subset,
                    confidence="Medium",
                    rationale="Adding an element cannot decrease the unique set size.",
                    domain_caveats="Non-empty inputs.",
                ))

        # Pattern 4: Fallback for arbitrary list/collection processing
        else:
            if len(params) == 1 or "items" in params or "data" in params or "loop" in ast_ops:
                r_idem = self.registry.get("MR_IDEMPOTENCE")
                if r_idem:
                    suggestions.append(SuggestedRelation(
                        relation=r_idem,
                        confidence="Low",
                        rationale="Candidate relation: Check whether the transformation is idempotent: f(f(x)) == f(x).",
                        domain_caveats="Verify whether the function output is intended to be idempotent.",
                    ))
                r_perm = self.registry.get("MR_PERMUTATION_INVARIANCE")
                if r_perm:
                    suggestions.append(SuggestedRelation(
                        relation=r_perm,
                        confidence="Low",
                        rationale="Candidate relation: Check whether element ordering affects output.",
                        domain_caveats="Only valid if problem is order-independent.",
                    ))

        return suggestions
