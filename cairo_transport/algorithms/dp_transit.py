"""Dynamic programming utilities for transit and maintenance planning."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from cairo_transport.algorithms.shortest_path import dijkstra
from cairo_transport.graph import Edge, TransportGraph
from cairo_transport.utils import tabulate


def optimize_bus_allocation(routes: list[dict[str, Any]], total_buses_budget: int) -> tuple[list[dict[str, Any]], int, list[list[int]]]:
    """Solve bus route selection with 0/1 knapsack DP.

    Complexity: O(n * W).
    """

    print(f"\n[DP Bus Allocation] Budget: {total_buses_budget} buses")
    print("[Complexity] O(n * W)")

    n_routes = len(routes)
    dp = [[0] * (total_buses_budget + 1) for _ in range(n_routes + 1)]

    for index in range(1, n_routes + 1):
        route = routes[index - 1]
        buses = int(route["buses_assigned"])
        value = int(route["daily_passengers"])
        for budget in range(total_buses_budget + 1):
            dp[index][budget] = dp[index - 1][budget]
            if buses <= budget:
                dp[index][budget] = max(dp[index][budget], dp[index - 1][budget - buses] + value)

    selected: list[dict[str, Any]] = []
    budget = total_buses_budget
    for index in range(n_routes, 0, -1):
        if dp[index][budget] != dp[index - 1][budget]:
            route = routes[index - 1]
            selected.append(route)
            budget -= int(route["buses_assigned"])
    selected.reverse()

    print(tabulate(
        [[route["id"], route["buses_assigned"], route["daily_passengers"], " -> ".join(route["stops"])] for route in selected],
        headers=["Route", "Buses", "Passengers", "Stops"],
        tablefmt="grid",
    ))
    print(f"Maximum passengers served: {dp[n_routes][total_buses_budget]:,}")
    return selected, dp[n_routes][total_buses_budget], dp


def road_maintenance_allocation(roads: list[Edge], budget_million_egp: int) -> tuple[list[dict[str, Any]], float]:
    """Allocate maintenance budget using integer DP on poor-condition roads.

    Complexity: O(n * W).
    """

    print(f"\n[DP Road Maintenance] Budget: {budget_million_egp} million EGP")
    print("[Complexity] O(n * W)")

    candidates: list[dict[str, Any]] = []
    for edge in roads:
        if edge.condition < 7:
            repair_cost = int(round(edge.distance * 10))
            repair_value = (10 - edge.condition) * edge.capacity
            candidates.append(
                {
                    "road": f"{edge.from_id}-{edge.to_id}",
                    "cost": repair_cost,
                    "value": repair_value,
                    "improvement": 10 - edge.condition,
                }
            )

    n_items = len(candidates)
    dp = [[0] * (budget_million_egp + 1) for _ in range(n_items + 1)]

    for index in range(1, n_items + 1):
        item = candidates[index - 1]
        for budget in range(budget_million_egp + 1):
            dp[index][budget] = dp[index - 1][budget]
            if item["cost"] <= budget:
                dp[index][budget] = max(dp[index][budget], dp[index - 1][budget - item["cost"]] + item["value"])

    selected: list[dict[str, Any]] = []
    budget = budget_million_egp
    for index in range(n_items, 0, -1):
        if dp[index][budget] != dp[index - 1][budget]:
            item = candidates[index - 1]
            selected.append(item)
            budget -= int(item["cost"])
    selected.reverse()

    total_improvement = sum(item["improvement"] for item in selected)
    print(tabulate(
        [[item["road"], item["cost"], item["value"], item["improvement"]] for item in selected],
        headers=["Road", "Repair Cost", "Impact Score", "Condition Gain"],
        tablefmt="grid",
    ))
    print(f"Expected total condition improvement points: {total_improvement:.1f}")
    return selected, total_improvement


def memoized_route_planner(
    graph: TransportGraph,
    source_id: str,
    targets_list: list[str],
    time_of_day: str = "morning",
) -> dict[str, Any]:
    """Cache shortest path computations for repeated source-target lookups."""

    stats = {"calls": 0}

    @lru_cache(maxsize=None)
    def cached(target_id: str) -> tuple[float, tuple[str, ...]]:
        stats["calls"] += 1
        cost, path, _ = dijkstra(graph, source_id, target_id, time_of_day)
        return cost, tuple(path)

    results: dict[str, Any] = {}
    for target in targets_list:
        cost, path = cached(target)
        results[target] = {"cost": cost, "path": list(path)}

    total_queries = len(targets_list)
    unique_queries = stats["calls"]
    hit_rate = (1 - unique_queries / total_queries) * 100 if total_queries else 0.0

    print("\n[Memoized Route Planner]")
    print(tabulate(
        [[target, round(data["cost"], 2), " -> ".join(data["path"])] for target, data in results.items()],
        headers=["Target", "Cost", "Path"],
        tablefmt="grid",
    ))
    print(f"Cache hit rate: {hit_rate:.2f}%")
    return {"results": results, "cache_hit_rate": hit_rate}
