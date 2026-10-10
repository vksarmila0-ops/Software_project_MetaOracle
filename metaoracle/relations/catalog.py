"""
Catalog of standard reusable metamorphic relations.
Includes Permutation, Symmetry, Idempotence, Scaling, Shift, and Add/Remove relations.
"""

import copy
import random
from typing import Any, List, Tuple
from .base import MetamorphicRelation, RelationCheckResult


class ReverseInputInvarianceRelation(MetamorphicRelation):
    """
    MR-1: Reverse-Input Invariance
    Property: Sorting or aggregating a list and its exact reverse must yield identical output.
    Domain: Ordered sequences where output is invariant to sequence direction (e.g. sort, sum).
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_REVERSE_INVARIANCE",
            name="Reverse-Input Invariance",
            category="Permutation",
            description="Reversing the input sequence should produce the exact same output: f(rev(x)) == f(x).",
            domain_requirements="Sequences (e.g., list of integers, floats, or strings).",
        )

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, (list, tuple)):
            return list(reversed(source_input))
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if source_output == follow_up_output:
            return RelationCheckResult(
                passed=True,
                message="Output is identical under input reversal.",
                expected_relation="f(rev(x)) == f(x)",
                actual_observation=f"Both outputs equal: {source_output}",
            )
        return RelationCheckResult(
            passed=False,
            message=(
                f"Violation: Reversing input altered output.\n"
                f"Source output: {source_output}\n"
                f"Follow-up output: {follow_up_output}"
            ),
            expected_relation="f(rev(x)) == f(x)",
            actual_observation=f"{source_output} != {follow_up_output}",
            details={
                "source_output": source_output,
                "follow_up_output": follow_up_output,
            },
        )


class PermutationInvarianceRelation(MetamorphicRelation):
    """
    MR-2: Permutation Invariance
    Property: Any arbitrary permutation (shuffle) of the input sequence yields identical output.
    Domain: Sorting, set conversion, multi-set operations, order-independent summaries.
    """

    def __init__(self, seed: int = 42):
        super().__init__(
            relation_id="MR_PERMUTATION_INVARIANCE",
            name="Permutation Invariance (Shuffle)",
            category="Permutation",
            description="Arbitrarily reordering elements must preserve output: f(perm(x)) == f(x).",
            domain_requirements="Sequences where elements have independent order semantics.",
        )
        self.rng = random.Random(seed)

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            shuffled = list(source_input)
            self.rng.shuffle(shuffled)
            return shuffled
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if source_output == follow_up_output:
            return RelationCheckResult(
                passed=True,
                message="Output is invariant to random permutation of input.",
                expected_relation="f(permute(x)) == f(x)",
                actual_observation="Both outputs equal.",
            )
        return RelationCheckResult(
            passed=False,
            message=(
                f"Violation: Shuffling input altered output.\n"
                f"Source output: {source_output}\n"
                f"Follow-up output: {follow_up_output}"
            ),
            expected_relation="f(permute(x)) == f(x)",
            actual_observation=f"{source_output} != {follow_up_output}",
            details={"diff": (source_output, follow_up_output)},
        )


class IdempotenceRelation(MetamorphicRelation):
    """
    MR-3: Idempotence Property
    Property: Applying the function twice to an input produces the exact same result
    as applying it once: f(f(x)) == f(x).
    Domain: Deduplication, sorting, normalization, canonicalization, formatting.
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_IDEMPOTENCE",
            name="Idempotence (f(f(x)) == f(x))",
            category="Idempotence",
            description="Re-applying the function to its own output should not alter the result: f(f(x)) == f(x).",
            domain_requirements="Functions whose domain and range are compatible.",
            is_output_derived=True,
        )

    def transform(self, source_output: Any) -> Any:
        # For idempotence, follow-up input is the source output!
        return copy.deepcopy(source_output)

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        # source_output is f(x), follow_up_output is f(f(x))
        if source_output == follow_up_output:
            return RelationCheckResult(
                passed=True,
                message="Function is idempotent: f(f(x)) == f(x).",
                expected_relation="f(f(x)) == f(x)",
                actual_observation=f"f(x) == f(f(x)) == {source_output}",
            )
        return RelationCheckResult(
            passed=False,
            message=(
                f"Violation: Function failed idempotence.\n"
                f"f(x) was: {source_output}\n"
                f"f(f(x)) was: {follow_up_output}"
            ),
            expected_relation="f(f(x)) == f(x)",
            actual_observation=f"{source_output} != {follow_up_output}",
            details={"f_x": source_output, "f_f_x": follow_up_output},
        )


class GraphSymmetryRelation(MetamorphicRelation):
    """
    MR-4: Undirected Graph Symmetry
    Property: In an undirected graph with symmetric weights, the shortest distance
    from node A to node B equals the distance from node B to node A:
    dist(G, A, B) == dist(G, B, A).
    Domain: Undirected graphs, symmetric metric spaces.
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_GRAPH_SYMMETRY",
            name="Undirected Graph Symmetry",
            category="Symmetry",
            description="Distance from A to B must equal distance from B to A in an undirected graph.",
            domain_requirements="Undirected graph tuple (graph, start_node, end_node).",
        )

    def transform(self, source_input: Any) -> Any:
        # source_input is (graph, start, end)
        if isinstance(source_input, (tuple, list)) and len(source_input) == 3:
            graph, start, end = source_input
            return (graph, end, start)
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if source_output == follow_up_output:
            return RelationCheckResult(
                passed=True,
                message="Shortest distance is symmetric: dist(A, B) == dist(B, A).",
                expected_relation="dist(G, A, B) == dist(G, B, A)",
                actual_observation=f"Both distances equal: {source_output}",
            )
        return RelationCheckResult(
            passed=False,
            message=(
                f"Violation: Graph distance is asymmetric!\n"
                f"dist({source_input[1]} -> {source_input[2]}) = {source_output}\n"
                f"dist({source_input[2]} -> {source_input[1]}) = {follow_up_output}"
            ),
            expected_relation="dist(G, A, B) == dist(G, B, A)",
            actual_observation=f"{source_output} != {follow_up_output}",
            details={
                "forward_dist": source_output,
                "reverse_dist": follow_up_output,
            },
        )


class ScalingProportionalityRelation(MetamorphicRelation):
    """
    MR-5: Scaling Proportionality
    Property: Multiplying all elements by a positive constant scalar k
    scales the sorted output by k: sort(k * x) == k * sort(x).
    Domain: Numeric sequences with order preservation under positive scalar multiplication.
    """

    def __init__(self, factor: int = 2):
        super().__init__(
            relation_id="MR_SCALING_PROPORTIONALITY",
            name=f"Scaling Proportionality (Factor k={factor})",
            category="Scaling",
            description=f"Scaling inputs by {factor} scales outputs predictably: f({factor} * x) == {factor} * f(x).",
            domain_requirements="Numeric lists with positive scalar k.",
        )
        self.factor = factor

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            return [x * self.factor for x in source_input]
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if isinstance(source_output, list) and isinstance(follow_up_output, list):
            expected = [x * self.factor for x in source_output]
            if follow_up_output == expected:
                return RelationCheckResult(
                    passed=True,
                    message="Outputs scaled proportionally as expected.",
                    expected_relation=f"f({self.factor} * x) == {self.factor} * f(x)",
                    actual_observation=f"Scaled output matches: {follow_up_output}",
                )
            return RelationCheckResult(
                passed=False,
                message=(
                    f"Violation: Scaling relation failed.\n"
                    f"Expected: {expected}\n"
                    f"Actual: {follow_up_output}"
                ),
                expected_relation=f"f({self.factor} * x) == {self.factor} * f(x)",
                actual_observation=f"{follow_up_output} != {expected}",
                details={"expected": expected, "actual": follow_up_output},
            )
        return RelationCheckResult(
            passed=False,
            message="Output type incompatible with scaling check.",
        )


class AdditiveShiftEquivarianceRelation(MetamorphicRelation):
    """
    MR-6: Additive Shift Equivariance
    Property: Adding a constant offset c to all elements shifts sorted output by c:
    sort(x + c) == sort(x) + c.
    Domain: Numeric sequences.
    """

    def __init__(self, shift: int = 5):
        super().__init__(
            relation_id="MR_ADDITIVE_SHIFT",
            name=f"Additive Shift Equivariance (+{shift})",
            category="Shift",
            description=f"Adding a constant {shift} shifts the output by {shift}: f(x + {shift}) == f(x) + {shift}.",
            domain_requirements="Numeric lists (integers or floats).",
        )
        self.shift = shift

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            return [x + self.shift for x in source_input]
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if isinstance(source_output, list) and isinstance(follow_up_output, list):
            expected = [x + self.shift for x in source_output]
            if follow_up_output == expected:
                return RelationCheckResult(
                    passed=True,
                    message="Additive shift equivariance holds.",
                    expected_relation=f"f(x + {self.shift}) == f(x) + {self.shift}",
                    actual_observation="Shifted outputs match expected offset.",
                )
            return RelationCheckResult(
                passed=False,
                message=f"Violation: Additive shift changed relative sorting or ordering.",
                expected_relation=f"f(x + {self.shift}) == f(x) + {self.shift}",
                actual_observation=f"{follow_up_output} != {expected}",
                details={"expected": expected, "actual": follow_up_output},
            )
        return RelationCheckResult(
            passed=False,
            message="Output type incompatible with additive shift check.",
        )


class DuplicateAmplificationInvarianceRelation(MetamorphicRelation):
    """
    MR-7: Duplicate Amplification Invariance
    Property: For deduplication, duplicating existing elements in the input
    should not change the set of unique elements or their relative first-seen order:
    dedup(double_elements(x)) == dedup(x).
    Domain: Deduplication and set conversion functions.
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_DUPLICATE_AMPLIFICATION",
            name="Duplicate Amplification Invariance",
            category="Add/Remove Data",
            description="Artificially multiplying duplicate occurrences of elements should not alter the deduplicated result.",
            domain_requirements="Iterables tested with deduplication.",
        )

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            # Double each element consecutively: [1, 2] -> [1, 1, 2, 2]
            res = []
            for item in source_input:
                res.extend([item, item])
            return res
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if source_output == follow_up_output:
            return RelationCheckResult(
                passed=True,
                message="Duplicate amplification preserved identical unique output.",
                expected_relation="dedup(amplified(x)) == dedup(x)",
                actual_observation="Both outputs equal.",
            )
        return RelationCheckResult(
            passed=False,
            message=(
                f"Violation: Adding duplicates changed deduplication output.\n"
                f"Source output: {source_output}\n"
                f"Follow-up output: {follow_up_output}"
            ),
            expected_relation="dedup(amplified(x)) == dedup(x)",
            actual_observation=f"{source_output} != {follow_up_output}",
            details={"diff": (source_output, follow_up_output)},
        )


class SubsetInclusionMonotonicityRelation(MetamorphicRelation):
    """
    MR-8: Subset Inclusion / Length Monotonicity
    Property: Appending an element to an input cannot decrease the output length of a sorting
    or deduplication function: len(f(x + [y])) >= len(f(x)).
    Domain: Non-lossy transformations, monotonic filters.
    """

    def __init__(self, item_to_add: int = 999):
        super().__init__(
            relation_id="MR_SUBSET_MONOTONICITY",
            name="Subset Length Monotonicity",
            category="Monotonicity",
            description="Appending an element must satisfy len(f(x + [y])) >= len(f(x)).",
            domain_requirements="Sequences with length-preserving or monotonic bounds.",
        )
        self.item_to_add = item_to_add

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            return list(source_input) + [self.item_to_add]
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if isinstance(source_output, (list, tuple)) and isinstance(follow_up_output, (list, tuple)):
            if len(follow_up_output) >= len(source_output):
                return RelationCheckResult(
                    passed=True,
                    message="Output length monotonically preserved.",
                    expected_relation="len(f(x + [y])) >= len(f(x))",
                    actual_observation=f"{len(follow_up_output)} >= {len(source_output)}",
                )
            return RelationCheckResult(
                passed=False,
                message=(
                    f"Violation: Appending an element decreased output length!\n"
                    f"Original length: {len(source_output)}, Follow-up length: {len(follow_up_output)}"
                ),
                expected_relation="len(f(x + [y])) >= len(f(x))",
                actual_observation=f"{len(follow_up_output)} < {len(source_output)}",
            )
class SizeConservationRelation(MetamorphicRelation):
    """
    MR-9: Size / Length Conservation
    Property: Sorting, shuffling, or non-filtering transformations must preserve the exact
    number of elements: len(f(x)) == len(x).
    Domain: Sorting, permutations, reversible transforms.
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_SIZE_CONSERVATION",
            name="Size / Length Conservation (len(f(x)) == len(x))",
            category="Conservation",
            description="The output length must exactly match input length: len(f(x)) == len(x).",
            domain_requirements="Transformations that must retain all elements (e.g. sorting).",
        )

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, (list, tuple)):
            # Follow-up: duplicate the input list items to verify conservation under duplicates
            return list(source_input) + list(source_input)
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if isinstance(source_input, (list, tuple)) and isinstance(source_output, (list, tuple)):
            if len(source_output) != len(source_input):
                return RelationCheckResult(
                    passed=False,
                    message=(
                        f"Violation: Output length does not match input length! Elements were dropped or duplicated.\n"
                        f"Input length: {len(source_input)}, Output length: {len(source_output)}"
                    ),
                    expected_relation="len(f(x)) == len(x)",
                    actual_observation=f"len(f(x))={len(source_output)} != len(x)={len(source_input)}",
                    details={"input_len": len(source_input), "output_len": len(source_output)},
                )
            if isinstance(follow_up_input, (list, tuple)) and isinstance(follow_up_output, (list, tuple)):
                if len(follow_up_output) != len(follow_up_input):
                    return RelationCheckResult(
                        passed=False,
                        message=(
                            f"Violation: Follow-up output dropped elements on duplicate input.\n"
                            f"Follow-up input length: {len(follow_up_input)}, Output length: {len(follow_up_output)}"
                        ),
                        expected_relation="len(f(x')) == len(x')",
                        actual_observation=f"len(f(x'))={len(follow_up_output)} != len(x')={len(follow_up_input)}",
                    )
            return RelationCheckResult(
                passed=True,
                message="Length conservation satisfied: len(f(x)) == len(x).",
                expected_relation="len(f(x)) == len(x)",
                actual_observation=f"Length {len(source_output)} conserved.",
            )
        return RelationCheckResult(passed=False, message="Inputs/outputs do not support len().")


class UniqueCompletenessRelation(MetamorphicRelation):
    """
    MR-10: Output Unique Completeness
    Property: In deduplication, all duplicate occurrences must be purged,
    so the result has no duplicate elements: len(f(x)) == len(set(f(x))).
    Domain: Deduplication and distinct filters.
    """

    def __init__(self):
        super().__init__(
            relation_id="MR_UNIQUE_COMPLETENESS",
            name="Unique Completeness (len(f(x)) == len(set(f(x))))",
            category="Deduplication",
            description="The output must contain zero duplicate elements: len(f(x)) == len(set(f(x))).",
            domain_requirements="Deduplication and distinct filter functions.",
        )

    def transform(self, source_input: Any) -> Any:
        if isinstance(source_input, list):
            # Follow-up: duplicate every element non-consecutively: [a, b] -> [a, b, a, b]
            return list(source_input) + list(source_input)
        return source_input

    def check(
        self,
        source_input: Any,
        follow_up_input: Any,
        source_output: Any,
        follow_up_output: Any,
    ) -> RelationCheckResult:
        if isinstance(source_output, list):
            unique_len = len(set(source_output))
            total_len = len(source_output)
            if total_len != unique_len:
                return RelationCheckResult(
                    passed=False,
                    message=(
                        f"Violation: Output contains leftover duplicates!\n"
                        f"Output length: {total_len}, Unique elements: {unique_len}.\n"
                        f"Output was: {source_output}"
                    ),
                    expected_relation="len(f(x)) == len(set(f(x)))",
                    actual_observation=f"Output has {total_len - unique_len} duplicate elements.",
                    details={"output": source_output},
                )
            # Also check follow up
            if isinstance(follow_up_output, list):
                f_uniq = len(set(follow_up_output))
                f_total = len(follow_up_output)
                if f_total != f_uniq:
                    return RelationCheckResult(
                        passed=False,
                        message=f"Violation: Follow-up output on non-consecutive duplicates retained duplicates: {follow_up_output}",
                        expected_relation="len(f(x')) == len(set(f(x')))",
                        actual_observation=f"Follow-up output has {f_total - f_uniq} duplicate elements.",
                    )
            return RelationCheckResult(
                passed=True,
                message="Output is completely unique without duplicate elements.",
                expected_relation="len(f(x)) == len(set(f(x)))",
                actual_observation="All elements unique.",
            )
        return RelationCheckResult(passed=False, message="Output is not a list.")

