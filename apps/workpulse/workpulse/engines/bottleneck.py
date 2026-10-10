"""Pure Python critical-path and bottleneck calculations for WorkPulse."""

from __future__ import annotations


def detect_cycle(graph: dict[str, list[str]]) -> bool:
    """Return True when a dependency graph contains a cycle."""
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in stack:
                return True
        stack.remove(node)
        return False

    for node in graph:
        if node not in visited and dfs(node):
            return True
    return False


def critical_path_length(graph: dict[str, list[str]], weights: dict[str, float]) -> float:
    """Return the longest weighted path in a DAG, measured in remaining effort."""
    if detect_cycle(graph):
        return 0.0

    memo: dict[str, float] = {}

    def longest(node: str) -> float:
        if node in memo:
            return memo[node]

        best = weights.get(node, 0.0)
        for neighbor in graph.get(node, []):
            best = max(best, weights.get(node, 0.0) + longest(neighbor))
        memo[node] = best
        return best

    return max((longest(node) for node in graph), default=0.0)
