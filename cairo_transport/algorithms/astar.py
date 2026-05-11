"""A* emergency routing for Cairo critical response scenarios."""

from __future__ import annotations

import heapq

from cairo_transport.graph import TransportGraph


def astar_emergency(
    graph: TransportGraph,
    source_id: str,
    target_facility_type: str = "Medical",
    time_of_day: str = "morning",
) -> tuple[list[str], float, int]:
    """Route an emergency vehicle to the nearest facility of the requested type.

    Complexity: O(E log V) average case.
    """

    print(f"\n[A* Emergency] Source: {graph.get_node(source_id).name} | Target type: {target_facility_type}")
    print("[Complexity] O(E log V) average case")

    targets = [node.id for node in graph.nodes.values() if node.node_type == target_facility_type]
    if not targets:
        print("No facility found for the requested type.")
        return [], 0.0, 0

    def heuristic(node_id: str) -> float:
        return min(graph.get_euclidean_distance(node_id, target) for target in targets)

    open_heap: list[tuple[float, float, str]] = [(heuristic(source_id), 0.0, source_id)]
    previous: dict[str, str] = {}
    g_score = {node_id: float("inf") for node_id in graph.nodes}
    g_score[source_id] = 0.0
    explored = 0
    destination = ""

    while open_heap:
        _, current_cost, current = heapq.heappop(open_heap)
        explored += 1
        if current in targets:
            destination = current
            break
        for edge, weight in graph.get_neighbors(current, time_of_day):
            emergency_weight = weight * 0.5
            tentative = current_cost + emergency_weight
            if tentative < g_score[edge.to_id]:
                g_score[edge.to_id] = tentative
                previous[edge.to_id] = current
                priority = tentative + heuristic(edge.to_id)
                heapq.heappush(open_heap, (priority, tentative, edge.to_id))

    if not destination:
        print("No emergency path available.")
        return [], 0.0, explored

    path = [destination]
    while path[-1] != source_id:
        path.append(previous[path[-1]])
    path.reverse()

    total_distance = sum(graph.get_edge(a, b).distance for a, b in zip(path, path[1:]) if graph.get_edge(a, b))
    estimated_time_minutes = total_distance

    print("Emergency path:", " -> ".join(graph.get_node(node_id).name for node_id in path))
    print(f"Estimated emergency travel time: {estimated_time_minutes:.2f} minutes")
    print(f"Nodes explored: {explored}")
    return path, estimated_time_minutes, explored
