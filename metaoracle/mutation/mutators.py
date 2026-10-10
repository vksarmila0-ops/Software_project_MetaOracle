"""
AST-based Mutation Operators for MetaOracle.
Generates syntactically valid mutants by modifying relational operators,
arithmetic operators, constants, logical connectors, and conditionals.
"""

import ast
import difflib
import textwrap
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass
class Mutant:
    """Represents an intentionally injected bug in source code."""
    mutant_id: str
    operator_name: str
    description: str
    line_number: int
    original_code: str
    mutated_code: str
    diff: str


class MutantGenerator:
    """Generates a collection of single-point syntactic mutants from Python source code."""

    def __init__(self):
        self.mutants: List[Mutant] = []
        self._counter = 0

    def generate_mutants(self, source_code: str, max_mutants: int = 25) -> List[Mutant]:
        """Parses source_code and returns a diverse list of distinct mutants."""
        self.mutants = []
        self._counter = 0

        clean_source = textwrap.dedent(source_code).strip()
        try:
            tree = ast.parse(clean_source)
        except (SyntaxError, IndentationError):
            return []

        # Find all candidate mutation targets
        candidates = self._find_mutation_candidates(tree)

        for candidate in candidates[:max_mutants]:
            mutated_tree = self._apply_mutation(tree, candidate)
            try:
                mutated_src = ast.unparse(mutated_tree)
                # Verify that mutated code is syntactically valid and actually different
                ast.parse(mutated_src)
                if mutated_src.strip() != source_code.strip():
                    self._counter += 1
                    diff = "".join(
                        difflib.unified_diff(
                            source_code.splitlines(keepends=True),
                            mutated_src.splitlines(keepends=True),
                            fromfile="original.py",
                            tofile=f"mutant_{self._counter}.py",
                        )
                    )
                    self.mutants.append(
                        Mutant(
                            mutant_id=f"MUTANT_{self._counter:02d}",
                            operator_name=candidate["operator"],
                            description=candidate["description"],
                            line_number=candidate["lineno"],
                            original_code=source_code,
                            mutated_code=mutated_src,
                            diff=diff,
                        )
                    )
            except Exception:
                continue

        return self.mutants

    def _find_mutation_candidates(self, tree: ast.AST) -> List[dict]:
        """Finds all nodes where a mutation operator can be applied."""
        candidates = []

        # Relational operator replacements (ROR)
        cmp_replacements = {
            ast.Gt: [ast.Lt, ast.GtE, ast.Eq],
            ast.Lt: [ast.Gt, ast.LtE, ast.Eq],
            ast.GtE: [ast.Lt, ast.Gt],
            ast.LtE: [ast.Gt, ast.Lt],
            ast.Eq: [ast.NotEq],
            ast.NotEq: [ast.Eq],
        }

        # Arithmetic operator replacements (AOR)
        bin_replacements = {
            ast.Add: [ast.Sub],
            ast.Sub: [ast.Add],
            ast.Mult: [ast.FloorDiv],
        }

        # Logical replacements (LCR)
        bool_replacements = {
            ast.And: [ast.Or],
            ast.Or: [ast.And],
        }

        for node in ast.walk(tree):
            lineno = getattr(node, "lineno", 1)

            # 1. ROR
            if isinstance(node, ast.Compare):
                for idx, op in enumerate(node.ops):
                    op_type = type(op)
                    if op_type in cmp_replacements:
                        for rep in cmp_replacements[op_type]:
                            candidates.append({
                                "node_id": id(node),
                                "operator": "ROR (Relational Operator Replacement)",
                                "description": f"Mutated comparison at line {lineno} to {rep.__name__}",
                                "lineno": lineno,
                                "type": "compare",
                                "target": node,
                                "op_idx": idx,
                                "new_op": rep(),
                            })

            # 2. AOR
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type in bin_replacements:
                    for rep in bin_replacements[op_type]:
                        candidates.append({
                            "node_id": id(node),
                            "operator": "AOR (Arithmetic Operator Replacement)",
                            "description": f"Mutated arithmetic operator at line {lineno} to {rep.__name__}",
                            "lineno": lineno,
                            "type": "binop",
                            "target": node,
                            "new_op": rep(),
                        })

            # 3. LCR
            elif isinstance(node, ast.BoolOp):
                op_type = type(node.op)
                if op_type in bool_replacements:
                    for rep in bool_replacements[op_type]:
                        candidates.append({
                            "node_id": id(node),
                            "operator": "LCR (Logical Connector Replacement)",
                            "description": f"Mutated boolean logic at line {lineno} to {rep.__name__}",
                            "lineno": lineno,
                            "type": "boolop",
                            "target": node,
                            "new_op": rep(),
                        })

            # 4. Constant Replacement (COR)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, bool):
                    candidates.append({
                        "node_id": id(node),
                        "operator": "COR (Boolean Constant Inversion)",
                        "description": f"Inverted boolean constant at line {lineno} to {not node.value}",
                        "lineno": lineno,
                        "type": "constant",
                        "target": node,
                        "new_val": not node.value,
                    })
                elif isinstance(node.value, int) and node.value in (0, 1):
                    new_val = 1 if node.value == 0 else 0
                    candidates.append({
                        "node_id": id(node),
                        "operator": "COR (Numeric Constant Replacement)",
                        "description": f"Replaced constant {node.value} at line {lineno} with {new_val}",
                        "lineno": lineno,
                        "type": "constant",
                        "target": node,
                        "new_val": new_val,
                    })

        return candidates

    def _apply_mutation(self, original_tree: ast.AST, candidate: dict) -> ast.AST:
        """Clones tree and applies the single mutation candidate."""
        # Deep clone AST
        tree_copy = ast.parse(ast.unparse(original_tree))

        target_lineno = candidate["lineno"]
        m_type = candidate["type"]

        class MutatorTransformer(ast.NodeTransformer):
            def __init__(self):
                super().__init__()
                self.applied = False

            def visit_Compare(self, node):
                self.generic_visit(node)
                if not self.applied and m_type == "compare" and node.lineno == target_lineno:
                    if candidate["op_idx"] < len(node.ops):
                        node.ops[candidate["op_idx"]] = candidate["new_op"]
                        self.applied = True
                return node

            def visit_BinOp(self, node):
                self.generic_visit(node)
                if not self.applied and m_type == "binop" and node.lineno == target_lineno:
                    node.op = candidate["new_op"]
                    self.applied = True
                return node

            def visit_BoolOp(self, node):
                self.generic_visit(node)
                if not self.applied and m_type == "boolop" and node.lineno == target_lineno:
                    node.op = candidate["new_op"]
                    self.applied = True
                return node

            def visit_Constant(self, node):
                self.generic_visit(node)
                if not self.applied and m_type == "constant" and getattr(node, "lineno", None) == target_lineno:
                    node.value = candidate["new_val"]
                    self.applied = True
                return node

        transformer = MutatorTransformer()
        return transformer.visit(tree_copy)
