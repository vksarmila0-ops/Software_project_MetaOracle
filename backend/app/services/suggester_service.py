"""
Service for static heuristic & AST-based Metamorphic Relation recommendations.
"""

from typing import List, Optional
from metaoracle.suggestion.suggester import RelationSuggester
from .preset_registry import get_preset_function, get_preset_code


def suggest_relations_for_target(
    category: Optional[str] = None,
    variant: Optional[str] = None,
    custom_code: Optional[str] = None,
) -> dict:
    """
    Analyzes Python AST and docstrings to suggest suitable Metamorphic Relations.
    """
    suggester = RelationSuggester()

    # Determine code to analyze
    code_to_analyze = ""
    fn_name = "target_function"

    if custom_code and custom_code.strip():
        code_to_analyze = custom_code
        fn_name = "custom_code"
    elif category and variant:
        fn = get_preset_function(category, variant)
        if fn:
            fn_name = fn.__name__
            code_to_analyze = get_preset_code(category, variant)
        else:
            code_to_analyze = get_preset_code("Sorting", "Correct Reference")

    if not code_to_analyze:
        code_to_analyze = 'def custom_function(items):\n    return sorted(items)\n'

    suggestions = suggester.suggest_from_code(code_to_analyze, target_fn_name=fn_name)

    items = []
    for s in suggestions:
        formula = getattr(s.relation, "formula", "")
        items.append({
            "relation_id": s.relation.relation_id,
            "relation_name": s.relation.name,
            "category": s.relation.category,
            "confidence": s.confidence,
            "rationale": s.rationale,
            "formula": formula,
            "domain_caveats": s.domain_caveats,
        })

    return {
        "function_name": fn_name,
        "suggestions": items,
    }
