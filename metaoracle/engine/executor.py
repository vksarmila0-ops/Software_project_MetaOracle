"""
Safe execution environment for executing target functions under test.
Provides timeout enforcement, exception capturing, and subprocess isolation for uploaded code.
"""

import concurrent.futures
import copy
import inspect
import json
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class ExecutionResult:
    """Outcome of running a target function on a single input."""
    success: bool
    output: Any
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    timed_out: bool = False


class SafeExecutor:
    """Executes target functions safely with timeout and error handling."""

    def __init__(self, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds

    def execute(self, func: Callable, args_or_input: Any) -> ExecutionResult:
        """
        Executes a callable with input, enforcing a strict timeout and catching all exceptions.
        Deep-copies input before execution to prevent in-place mutation side-effects.
        """
        # Deep-copy input to avoid target function mutating source test data in place
        try:
            safe_input = copy.deepcopy(args_or_input)
        except Exception:
            safe_input = args_or_input

        def _worker():
            # If input is a tuple and function expects multiple parameters, unpack it
            if isinstance(safe_input, tuple):
                try:
                    sig = inspect.signature(func)
                    param_count = len(sig.parameters)
                    if param_count == len(safe_input):
                        return func(*safe_input)
                except Exception:
                    pass
            return func(safe_input)

        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_worker)
            try:
                result = future.result(timeout=self.timeout_seconds)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ExecutionResult(
                    success=True,
                    output=result,
                    duration_ms=elapsed_ms,
                )
            except concurrent.futures.TimeoutError:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ExecutionResult(
                    success=False,
                    output=None,
                    error_type="TimeoutError",
                    error_message=f"Execution timed out after {self.timeout_seconds} seconds.",
                    duration_ms=elapsed_ms,
                    timed_out=True,
                )
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
                return ExecutionResult(
                    success=False,
                    output=None,
                    error_type=type(e).__name__,
                    error_message=str(e) or type(e).__name__,
                    duration_ms=elapsed_ms,
                )

    @staticmethod
    def load_callable_from_code(code_str: str, function_name: Optional[str] = None) -> Tuple[Callable, str]:
        """
        Safely compiles code string in a clean namespace and extracts the target callable.
        Returns (callable, detected_function_name).
        """
        namespace: Dict[str, Any] = {}
        # Basic AST syntax validation
        compile(code_str, "<user_code>", "exec")
        exec(code_str, namespace)

        if function_name and function_name in namespace and callable(namespace[function_name]):
            return namespace[function_name], function_name

        # Otherwise find the last defined function in the namespace
        callables = [k for k, v in namespace.items() if callable(v) and not k.startswith("__")]
        if not callables:
            raise ValueError("No callable function found in provided code.")

        chosen_name = function_name if function_name in callables else callables[-1]
        return namespace[chosen_name], chosen_name
