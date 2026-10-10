"""Metamorphic Relations package."""

from .base import MetamorphicRelation, RelationCheckResult
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
from .registry import RelationRegistry, default_registry

__all__ = [
    "MetamorphicRelation",
    "RelationCheckResult",
    "ReverseInputInvarianceRelation",
    "PermutationInvarianceRelation",
    "IdempotenceRelation",
    "GraphSymmetryRelation",
    "ScalingProportionalityRelation",
    "AdditiveShiftEquivarianceRelation",
    "DuplicateAmplificationInvarianceRelation",
    "SubsetInclusionMonotonicityRelation",
    "SizeConservationRelation",
    "UniqueCompletenessRelation",
    "RelationRegistry",
    "default_registry",
]
