"""Greedy algorithms for traffic signal timing and emergency preemption."""

from __future__ import annotations

from cairo_transport.graph import TransportGraph
from cairo_transport.utils import tabulate


def optimize_traffic_signals(graph: TransportGraph, intersection_node_id: str, time_of_day: str) -> dict[str, object]:
    """Assign green-light time greedily by congestion ratio.

    Complexity: O(degree(v) log degree(v)).
    """

    print(f"\n[Greedy Signals] Intersection: {graph.get_node(intersection_node_id).name}")
    print("[Complexity] O(degree(v) log degree(v))")

    incoming = graph.get_incoming_edges(intersection_node_id)
    ranked = sorted(
        incoming,
        key=lambda edge: edge.traffic.get(time_of_day, 0) / edge.capacity if edge.capacity else 0,
        reverse=True,
    )

    total_rank = sum(range(1, len(ranked) + 1)) or 1
    signal_plan: dict[str, int] = {}
    critical_roads: list[str] = []

    for index, edge in enumerate(ranked, start=1):
        reverse_rank = len(ranked) - index + 1
        green_time = int(30 + (reverse_rank / total_rank) * 90)
        road_id = f"{edge.from_id}->{edge.to_id}"
        signal_plan[road_id] = green_time
        ratio = edge.traffic.get(time_of_day, 0) / edge.capacity if edge.capacity else 0
        if ratio > 0.9:
            critical_roads.append(road_id)

    print(tabulate(
        [[road, seconds] for road, seconds in signal_plan.items()],
        headers=["Incoming Road", "Green Time (sec)"],
        tablefmt="grid",
    ))
    print(f"Critical roads: {', '.join(critical_roads) if critical_roads else 'None'}")
    return {"signal_plan": signal_plan, "critical_roads": critical_roads}


def emergency_preemption(graph: TransportGraph, emergency_path: list[str], time_of_day: str) -> tuple[list[dict[str, object]], float]:
    """Simulate signal preemption along an emergency route."""

    preemption_schedule: list[dict[str, object]] = []
    total_delay = 0.0

    for current, nxt in zip(emergency_path, emergency_path[1:]):
        affected = [edge for edge in graph.get_incoming_edges(nxt) if edge.from_id != current]
        delay = sum((edge.traffic.get(time_of_day, 0) / max(edge.capacity, 1)) * 2 for edge in affected)
        total_delay += delay
        preemption_schedule.append(
            {
                "intersection": graph.get_node(nxt).name,
                "priority_road": f"{graph.get_node(current).name} -> {graph.get_node(nxt).name}",
                "cross_traffic_red": len(affected),
                "delay_seconds": round(delay, 2),
            }
        )

    print("\n[Emergency Preemption]")
    print(tabulate(
        [[item["intersection"], item["priority_road"], item["cross_traffic_red"], item["delay_seconds"]] for item in preemption_schedule],
        headers=["Intersection", "Priority Road", "Cross Roads Held", "Delay to Others (sec)"],
        tablefmt="grid",
    ))
    print(f"Total delay imposed on others: {total_delay:.2f} seconds")
    return preemption_schedule, total_delay
