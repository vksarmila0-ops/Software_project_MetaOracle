"""
Relation registry for MetaOracle: stores, retrieves, and categorizes metamorphic relations.
"""

from typing import Dict, List, Optional
from .base import MetamorphicRelation
from .catalog import (
    ReverseInputInvarianceRelation,
    PermutationInvarianceRelation,
    IdempotenceRelation,
    GraphSymmetryRelation,
    ScalingProportionalityRelation,
    AdditiveShiftEquivarianceRelation,
    DuplicateAmplificationInvarianceRelation,
    SubsetInclusionMonotonicityRelation,
    SizeConservationRelation,
    UniqueCompletenessRelation,
)


class RelationRegistry:
    """Central store of all registered metamorphic relations."""

    def __init__(self):
        self._relations: Dict[str, MetamorphicRelation] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            ReverseInputInvarianceRelation(),
            PermutationInvarianceRelation(),
            IdempotenceRelation(),
            GraphSymmetryRelation(),
            ScalingProportionalityRelation(),
            AdditiveShiftEquivarianceRelation(),
            DuplicateAmplificationInvarianceRelation(),
            SubsetInclusionMonotonicityRelation(),
            SizeConservationRelation(),
            UniqueCompletenessRelation(),
        ]
        for rel in defaults:
            self.register(rel)

    def register(self, relation: MetamorphicRelation):
        self._relations[relation.relation_id] = relation

    def get(self, relation_id: str) -> Optional[MetamorphicRelation]:
        return self._relations.get(relation_id)

    def list_all(self) -> List[MetamorphicRelation]:
        return list(self._relations.values())

    def by_category(self, category: str) -> List[MetamorphicRelation]:
        return [r for r in self._relations.values() if r.category.lower() == category.lower()]

    def get_summary(self) -> List[Dict[str, str]]:
        return [
            {
                "id": r.relation_id,
                "name": r.name,
                "category": r.category,
                "description": r.description,
                "domain_requirements": r.domain_requirements,
            }
            for r in self._relations.values()
        ]


# Global singleton instance
default_registry = RelationRegistry()
