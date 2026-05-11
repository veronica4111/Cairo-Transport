"""Shortest path algorithms for congestion-aware routing."""

from __future__ import annotations

import heapq
from typing import Any

from cairo_transport.data import TIME_SLOTS
from cairo_transport.graph import Edge, TransportGraph
from cairo_transport.utils import tabulate


def _format_path(graph: TransportGraph, path: list[str]) -> str:
    """Format a node path using human-readable names."""
    return " -> ".join(graph.get_node(node_id).name for node_id in path)


def _reconstruct_path(previous: dict[str, str], source_id: str, target_id: str) -> list[str]:
    """Reconstruct a path from predecessor links."""
    if target_id not in previous and target_id != source_id:
        return []
    path = [target_id]
    current = target_id
    while current != source_id:
        current = previous[current]
        path.append(current)
    path.reverse()
    return path


def _edge_report(edge: Edge, time_of_day: str, graph: TransportGraph) -> dict[str, Any]:
    """Build a per-edge congestion report record."""
    flow = edge.traffic.get(time_of_day, 0)
    percent = (flow / edge.capacity * 100) if edge.capacity else 0
    return {
        "edge": f"{graph.get_node(edge.from_id).name} -> {graph.get_node(edge.to_id).name}",
        "distance_km": round(edge.distance, 2),
        "congestion_pct": round(percent, 1),
        "flow": flow,
        "capacity": edge.capacity,
    }


def dijkstra(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    time_of_day: str = "morning",
    blocked_edges: set[frozenset[str]] | None = None,
    use_metro: bool = False,
    metro_lines: list[dict[str, Any]] | None = None,
) -> tuple[float, list[str], list[dict[str, Any]]]:
    """Run congestion-aware Dijkstra's algorithm.

    Complexity: O((V + E) log V).
    
    Args:
        graph: Transport graph
        source_id: Starting node
        target_id: Destination node
        time_of_day: Time slot for traffic weights
        blocked_edges: Set of blocked edges to avoid
        use_metro: Whether to consider metro lines as alternative routes
        metro_lines: List of metro line data with stations
    """

    print(f"\n[Dijkstra] {graph.get_node(source_id).name} -> {graph.get_node(target_id).name} at {time_of_day}")
    print("[Complexity] O((V + E) log V)")

    blocked_edges = blocked_edges or set()
    distances = {node_id: float("inf") for node_id in graph.nodes}
    previous: dict[str, str] = {}
    distances[source_id] = 0.0
    heap: list[tuple[float, str]] = [(0.0, source_id)]
    
    # Build metro adjacency for rush hour optimization
    metro_adjacency: dict[str, list[tuple[str, float]]] = {}
    if use_metro and metro_lines and time_of_day in ("morning", "evening"):
        for line in metro_lines:
            stations = line.get("stations", [])
            # Metro has fixed low travel time regardless of congestion
            for i in range(len(stations) - 1):
                metro_adjacency.setdefault(stations[i], []).append((stations[i + 1], 3.0))
                metro_adjacency.setdefault(stations[i + 1], []).append((stations[i], 3.0))

    while heap:
        current_cost, current = heapq.heappop(heap)
        if current_cost > distances[current]:
            continue
        if current == target_id:
            break
        
        # Regular road edges
        for edge, weight in graph.get_neighbors(current, time_of_day):
            if frozenset((edge.from_id, edge.to_id)) in blocked_edges:
                continue
            new_cost = current_cost + weight
            if new_cost < distances[edge.to_id]:
                distances[edge.to_id] = new_cost
                previous[edge.to_id] = current
                heapq.heappush(heap, (new_cost, edge.to_id))
        
        # Metro edges (only during rush hour)
        if current in metro_adjacency:
            for neighbor, metro_weight in metro_adjacency[current]:
                new_cost = current_cost + metro_weight
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current
                    heapq.heappush(heap, (new_cost, neighbor))

    path = _reconstruct_path(previous, source_id, target_id)
    if not path:
        print("No route available.")
        return float("inf"), [], []

    report: list[dict[str, Any]] = []
    for start, end in zip(path, path[1:]):
        edge = graph.get_edge(start, end)
        if edge is not None:
            report.append(_edge_report(edge, time_of_day, graph))

    print(f"Best path: {_format_path(graph, path)}")
    print(f"Total congestion cost: {distances[target_id]:.2f}")
    print(tabulate(
        [[row["edge"], row["distance_km"], row["flow"], row["capacity"], f'{row["congestion_pct"]}%'] for row in report],
        headers=["Step", "Distance (km)", "Flow", "Capacity", "Congestion"],
        tablefmt="grid",
    ))
    return distances[target_id], path, report


def time_aware_dijkstra(graph: TransportGraph, source_id: str, target_id: str, metro_lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compare Dijkstra routing across all time slots with optional metro support."""

    print("\n[Time-Aware Dijkstra] Comparing four time slots")
    results: dict[str, Any] = {}
    road_congestion_by_time: dict[str, list[float]] = {}

    for slot in TIME_SLOTS:
        # Use metro during rush hours
        use_metro = slot in ("morning", "evening")
        cost, path, report = dijkstra(graph, source_id, target_id, time_of_day=slot, use_metro=use_metro, metro_lines=metro_lines)
        results[slot] = {"cost": cost, "path": path, "report": report}
        for row in report:
            road_congestion_by_time.setdefault(row["edge"], []).append(float(row["congestion_pct"]))

    comparison = [
        [slot, round(data["cost"], 2), _format_path(graph, data["path"]) if data["path"] else "No route"]
        for slot, data in results.items()
    ]
    flips = [road for road, values in road_congestion_by_time.items() if values and min(values) < 85 < max(values)]

    print(tabulate(comparison, headers=["Time Slot", "Cost", "Path"], tablefmt="grid"))
    print(f"Roads that flip into heavy congestion: {', '.join(flips) if flips else 'None'}")
    return {"results": results, "comparison": comparison, "flipping_roads": flips}


def find_alternate_route(
    graph: TransportGraph,
    source_id: str,
    target_id: str,
    blocked_edges: list[tuple[str, str]],
    time_of_day: str,
) -> tuple[float, list[str], list[dict[str, Any]]] | str:
    """Temporarily block roads and search for an alternate route."""
    blocked = {frozenset(edge) for edge in blocked_edges}
    result = dijkstra(graph, source_id, target_id, time_of_day=time_of_day, blocked_edges=blocked)
    if not result[1]:
        return "no route available"
    return result


def route_to_airport(graph: TransportGraph, source_id: str, time_of_day: str = "morning") -> dict[str, Any]:
    """Find fastest route to Cairo International Airport (F1) from any given node.
    
    This is a specialized routing function for airport access planning.
    
    Args:
        graph: Transport graph
        source_id: Starting node ID
        time_of_day: Time slot for traffic weights
        
    Returns:
        Dictionary with path, distance, estimated time, and route details
    """
    airport_id = "F1"
    
    print(f"\n[Airport Access] Route from {graph.get_node(source_id).name} to Cairo International Airport")
    
    cost, path, report = dijkstra(graph, source_id, airport_id, time_of_day)
    
    if not path:
        return {
            "success": False,
            "message": "No route to airport available",
            "source": graph.get_node(source_id).name,
            "airport": "Cairo International Airport",
        }
    
    total_distance = sum(r["distance_km"] for r in report)
    avg_congestion = sum(r["congestion_pct"] for r in report) / len(report) if report else 0
    
    # Estimate travel time based on distance and congestion
    # Base speed 50 km/h, reduced by congestion
    effective_speed = 50 * (1 - avg_congestion / 200)
    estimated_time = (total_distance / max(effective_speed, 10)) * 60  # minutes
    
    path_names = [graph.get_node(nid).name for nid in path]
    
    print(f"Best route: {' → '.join(path_names)}")
    print(f"Total distance: {total_distance:.2f} km")
    print(f"Estimated time: {estimated_time:.1f} minutes")
    print(f"Average congestion: {avg_congestion:.1f}%")
    
    return {
        "success": True,
        "source": graph.get_node(source_id).name,
        "airport": "Cairo International Airport",
        "path": path,
        "path_names": path_names,
        "total_distance": round(total_distance, 2),
        "estimated_time": round(estimated_time, 1),
        "avg_congestion": round(avg_congestion, 1),
        "congestion_cost": round(cost, 2),
        "route_details": report,
    }
