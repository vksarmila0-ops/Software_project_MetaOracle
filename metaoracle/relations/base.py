"""
Base abstractions for Metamorphic Relations (MR) in MetaOracle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class RelationCheckResult:
    """Represents the outcome of checking a metamorphic relation."""
    passed: bool
    message: str
    expected_relation: str = ""
    actual_observation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "message": self.message,
            "expected_relation": self.expected_relation,
            "actual_observation": self.actual_observation,
            "details": self.details,
        }


class MetamorphicRelation(ABC):
    """
    Abstract base class for a Metamorphic Relation (MR).
    
    A metamorphic relation specifies:
    1. A transformation of source inputs into follow-up inputs: x -> x'
       (or an output-derived transformation where x' = f(x)).
    2. A checking condition verifying whether (x, x', y, y') satisfies the property.
    """

    def __init__(
        self,
        relation_id: str,
        name: str,
        category: str,
        description: str,
        domain_requirements: str = "",
        is_output_derived: bool = False,
    ):
        self.relation_id = relation_id
        self.name = name
        self.category = category
        self.description = description
        self.domain_requirements = domain_requirements
        self.is_output_derived = is_output_derived

    @abstractmethod
    def transform(self, source_input: Any) -> Any:
        """
        Transforms a source input into a follow-up input.
        If is_output_derived is True, this receives source_output instead.
        """
        pass

    @abstractmethod
    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        """
        Checks whether the metamorphic property holds between source and follow-up executions.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.relation_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "domain_requirements": self.domain_requirements,
            "is_output_derived": self.is_output_derived,
        }

    def __repr__(self) -> str:
        return f"<MetamorphicRelation {self.relation_id}: {self.name}>"
