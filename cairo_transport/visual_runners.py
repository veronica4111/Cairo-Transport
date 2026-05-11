"""Visualization-only algorithm runners.

These helpers are intentionally separate from the production algorithm modules.
They produce step-by-step traces for the UI while leaving the original
Dijkstra, A*, and graph data structures untouched.
"""

from __future__ import annotations

import heapq
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

from cairo_transport.graph import TransportGraph

VisualAlgorithm = Literal["dijkstra", "astar", "greedy", "bfs"]


@dataclass(frozen=True)
class VisualStep:
    """One animation frame for the side-by-side visualizer."""

    current: str
    visited: list[str]
    frontier: list[str]
    path: list[str]


def _reconstruct_path(previous: dict[str, str], source_id: str, target_id: str) -> list[str]:
    if target_id not in previous and target_id != source_id:
        return []
    path = [target_id]
    current = target_id
    while current != source_id:
        current = previous[current]
        path.append(current)
    path.reverse()
    return path


def _path_distance(graph: TransportGraph, path: list[str]) -> float:
    total = 0.0
    for start, end in zip(path, path[1:]):
        edge = graph.get_edge(start, end)
        if edge is not None:
            total += edge.distance
    return total


def _serialize_step(step: VisualStep) -> dict[str, Any]:
    return {
        "current": step.current,
        "visited": step.visited,
        "frontier": step.frontier,
        "path": step.path,
    }


def trace_dijkstra(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Create a Dijkstra trace for visualization only."""

    started = time.perf_counter()
    distances = {node_id: float("inf") for node_id in graph.nodes}
    previous: dict[str, str] = {}
    distances[source_id] = 0.0
    heap: list[tuple[float, str]] = [(0.0, source_id)]
    visited_order: list[str] = []
    visited_set: set[str] = set()
    steps: list[VisualStep] = []
    peak_frontier = 1

    while heap:
        current_cost, current = heapq.heappop(heap)
        if current in visited_set or current_cost > distances[current]:
            continue

        visited_set.add(current)
        visited_order.append(current)

        if current == target_id:
            steps.append(
                VisualStep(
                    current=current,
                    visited=list(visited_order),
                    frontier=[item[1] for item in heap if item[1] not in visited_set],
                    path=_reconstruct_path(previous, source_id, target_id),
                )
            )
            break

        for edge, weight in graph.get_neighbors(current, time_of_day):
            new_cost = current_cost + weight
            if new_cost < distances[edge.to_id]:
                distances[edge.to_id] = new_cost
                previous[edge.to_id] = current
                heapq.heappush(heap, (new_cost, edge.to_id))

        peak_frontier = max(peak_frontier, len(heap))
        steps.append(
            VisualStep(
                current=current,
                visited=list(visited_order),
                frontier=[item[1] for item in heap if item[1] not in visited_set],
                path=_reconstruct_path(previous, source_id, current),
            )
        )

    final_path = _reconstruct_path(previous, source_id, target_id)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "algorithm": "dijkstra",
        "label": "Dijkstra",
        "steps": [_serialize_step(step) for step in steps],
        "final_path": final_path,
        "cost": round(distances.get(target_id, float("inf")), 4),
        "path_length": round(_path_distance(graph, final_path), 4),
        "visited_count": len(visited_order),
        "execution_time_ms": round(elapsed_ms, 4),
        "memory_units": peak_frontier + len(previous) + len(visited_set),
    }


def trace_astar(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Create an A* trace for visualization only.

    The production A* implementation routes to a nearest facility type. This
    visualization runner uses the same graph weights plus the existing
    Euclidean heuristic to compare target-to-target behavior in the UI.
    """

    started = time.perf_counter()

    def heuristic(node_id: str) -> float:
        return graph.get_euclidean_distance(node_id, target_id)

    open_heap: list[tuple[float, float, str]] = [(heuristic(source_id), 0.0, source_id)]
    g_score = {node_id: float("inf") for node_id in graph.nodes}
    g_score[source_id] = 0.0
    previous: dict[str, str] = {}
    visited_order: list[str] = []
    visited_set: set[str] = set()
    steps: list[VisualStep] = []
    peak_frontier = 1

    while open_heap:
        _, current_cost, current = heapq.heappop(open_heap)
        if current in visited_set or current_cost > g_score[current]:
            continue

        visited_set.add(current)
        visited_order.append(current)

        if current == target_id:
            steps.append(
                VisualStep(
                    current=current,
                    visited=list(visited_order),
                    frontier=[item[2] for item in open_heap if item[2] not in visited_set],
                    path=_reconstruct_path(previous, source_id, target_id),
                )
            )
            break

        for edge, weight in graph.get_neighbors(current, time_of_day):
            tentative = current_cost + weight
            if tentative < g_score[edge.to_id]:
                g_score[edge.to_id] = tentative
                previous[edge.to_id] = current
                heapq.heappush(open_heap, (tentative + heuristic(edge.to_id), tentative, edge.to_id))

        peak_frontier = max(peak_frontier, len(open_heap))
        steps.append(
            VisualStep(
                current=current,
                visited=list(visited_order),
                frontier=[item[2] for item in open_heap if item[2] not in visited_set],
                path=_reconstruct_path(previous, source_id, current),
            )
        )

    final_path = _reconstruct_path(previous, source_id, target_id)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "algorithm": "astar",
        "label": "A*",
        "steps": [_serialize_step(step) for step in steps],
        "final_path": final_path,
        "cost": round(g_score.get(target_id, float("inf")), 4),
        "path_length": round(_path_distance(graph, final_path), 4),
        "visited_count": len(visited_order),
        "execution_time_ms": round(elapsed_ms, 4),
        "memory_units": peak_frontier + len(previous) + len(visited_set),
    }


def trace_greedy_best_first(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Create a Greedy Best-First trace for visualization only.

    Greedy search prioritizes the node that looks closest to the target by
    heuristic distance. It is fast to visualize, but it does not guarantee the
    lowest weighted route cost.
    """

    started = time.perf_counter()

    def heuristic(node_id: str) -> float:
        return graph.get_euclidean_distance(node_id, target_id)

    open_heap: list[tuple[float, str]] = [(heuristic(source_id), source_id)]
    previous: dict[str, str] = {}
    visited_order: list[str] = []
    visited_set: set[str] = set()
    queued = {source_id}
    steps: list[VisualStep] = []
    peak_frontier = 1

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in visited_set:
            continue

        visited_set.add(current)
        visited_order.append(current)

        if current == target_id:
            steps.append(
                VisualStep(
                    current=current,
                    visited=list(visited_order),
                    frontier=[item[1] for item in open_heap if item[1] not in visited_set],
                    path=_reconstruct_path(previous, source_id, target_id),
                )
            )
            break

        for edge, _ in graph.get_neighbors(current, time_of_day):
            if edge.to_id in visited_set or edge.to_id in queued:
                continue
            previous[edge.to_id] = current
            queued.add(edge.to_id)
            heapq.heappush(open_heap, (heuristic(edge.to_id), edge.to_id))

        peak_frontier = max(peak_frontier, len(open_heap))
        steps.append(
            VisualStep(
                current=current,
                visited=list(visited_order),
                frontier=[item[1] for item in open_heap if item[1] not in visited_set],
                path=_reconstruct_path(previous, source_id, current),
            )
        )

    final_path = _reconstruct_path(previous, source_id, target_id)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "algorithm": "greedy",
        "label": "Greedy Best-First",
        "steps": [_serialize_step(step) for step in steps],
        "final_path": final_path,
        "cost": round(sum(weight for a, b in zip(final_path, final_path[1:]) for edge, weight in graph.get_neighbors(a, time_of_day) if edge.to_id == b), 4),
        "path_length": round(_path_distance(graph, final_path), 4),
        "visited_count": len(visited_order),
        "execution_time_ms": round(elapsed_ms, 4),
        "memory_units": peak_frontier + len(previous) + len(visited_set),
    }


def trace_bfs(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Create a BFS trace for visualization only.

    BFS ignores road distance and congestion. It finds the path with the fewest
    road hops, which is useful as an educational contrast against weighted
    transportation routing.
    """

    started = time.perf_counter()
    queue: deque[str] = deque([source_id])
    previous: dict[str, str] = {}
    visited_order: list[str] = []
    visited_set: set[str] = {source_id}
    steps: list[VisualStep] = []
    peak_frontier = 1

    while queue:
        current = queue.popleft()
        visited_order.append(current)

        if current == target_id:
            steps.append(
                VisualStep(
                    current=current,
                    visited=list(visited_order),
                    frontier=list(queue),
                    path=_reconstruct_path(previous, source_id, target_id),
                )
            )
            break

        for edge, _ in graph.get_neighbors(current, time_of_day):
            if edge.to_id in visited_set:
                continue
            visited_set.add(edge.to_id)
            previous[edge.to_id] = current
            queue.append(edge.to_id)

        peak_frontier = max(peak_frontier, len(queue))
        steps.append(
            VisualStep(
                current=current,
                visited=list(visited_order),
                frontier=list(queue),
                path=_reconstruct_path(previous, source_id, current),
            )
        )

    final_path = _reconstruct_path(previous, source_id, target_id)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "algorithm": "bfs",
        "label": "Breadth-First Search",
        "steps": [_serialize_step(step) for step in steps],
        "final_path": final_path,
        "cost": round(sum(weight for a, b in zip(final_path, final_path[1:]) for edge, weight in graph.get_neighbors(a, time_of_day) if edge.to_id == b), 4),
        "path_length": round(_path_distance(graph, final_path), 4),
        "visited_count": len(visited_order),
        "execution_time_ms": round(elapsed_ms, 4),
        "memory_units": peak_frontier + len(previous) + len(visited_set),
    }


def run_visual_trace(
    graph: TransportGraph,
    algorithm: VisualAlgorithm,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Dispatch a visualization-only algorithm trace."""

    if algorithm == "dijkstra":
        return trace_dijkstra(graph, source_id, target_id, time_of_day)
    if algorithm == "astar":
        return trace_astar(graph, source_id, target_id, time_of_day)
    if algorithm == "greedy":
        return trace_greedy_best_first(graph, source_id, target_id, time_of_day)
    if algorithm == "bfs":
        return trace_bfs(graph, source_id, target_id, time_of_day)
    raise ValueError(f"Unsupported visual algorithm: {algorithm}")
