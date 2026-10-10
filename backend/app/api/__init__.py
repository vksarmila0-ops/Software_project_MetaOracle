"""
API Routes Package.
"""
from .routes_tests import router as tests_router
from .routes_relations import router as relations_router
from .routes_mutation import router as mutation_router
from .routes_benchmark import router as benchmark_router
from .routes_snippets import router as snippets_router
from .routes_stats import router as stats_router

__all__ = [
    "tests_router",
    "relations_router",
    "mutation_router",
    "benchmark_router",
    "snippets_router",
    "stats_router",
]
