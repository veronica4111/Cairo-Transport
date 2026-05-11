"""Modified Kruskal MST for Cairo infrastructure design."""

from __future__ import annotations

from dataclasses import dataclass

from cairo_transport.data import MANDATORY_MST_NODE_IDS
from cairo_transport.graph import Edge, TransportGraph
from cairo_transport.utils import tabulate


class UnionFind:
    """Union-Find with path compression and union by rank."""

    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}
        self.rank = {item: 0 for item in items}

    def find(self, item: str) -> str:
        """Find the root representative of an item."""
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1: str, item2: str) -> bool:
        """Union two sets and return True when a merge happens."""
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 == root2:
            return False
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
        return True


@dataclass
class MSTResult:
    """Store the modified MST output bundle."""

    edges: list[Edge]
    total_distance: float
    total_cost_estimate: float
    mandatory_edges: list[Edge]
    suggested_new_roads: list[dict[str, float | str]]


def _mst_weight(edge: Edge) -> float:
    """Weight roads by quality-adjusted distance."""
    return edge.distance / max(edge.condition, 1)


def _best_existing_connection(graph: TransportGraph, node_id: str) -> Edge | None:
    """Return the best existing road adjacent to a mandatory node."""
    neighbors = [edge for edge in graph.adjacency.get(node_id, []) if edge.is_existing]
    if not neighbors:
        return None
    return min(neighbors, key=_mst_weight)


def modified_kruskal_mst(graph: TransportGraph) -> MSTResult:
    """Run Kruskal with mandatory facility connectivity.

    Complexity: O(E log E) for sorting plus O(E alpha(V)) for Union-Find.
    """

    print("\n[MST] Running modified Kruskal's algorithm")
    print("[Complexity] O(E log E) + O(E alpha(V))")

    uf = UnionFind(list(graph.nodes.keys()))
    mst_edges: list[Edge] = []
    mandatory_edges: list[Edge] = []
    included_keys: set[frozenset[str]] = set()

    for node_id in MANDATORY_MST_NODE_IDS:
        edge = _best_existing_connection(graph, node_id)
        if edge is None:
            continue
        key = frozenset((edge.from_id, edge.to_id))
        if key in included_keys:
            continue
        if uf.union(edge.from_id, edge.to_id):
            mst_edges.append(edge)
            mandatory_edges.append(edge)
            included_keys.add(key)

    for edge in sorted(graph.get_all_edges(existing_only=True), key=_mst_weight):
        key = frozenset((edge.from_id, edge.to_id))
        if key in included_keys:
            continue
        if uf.union(edge.from_id, edge.to_id):
            mst_edges.append(edge)
            included_keys.add(key)

    suggestions = sorted(
        (
            {
                "road": f"{edge.from_id} <-> {edge.to_id}",
                "distance_km": float(edge.distance),
                "construction_cost": float(edge.construction_cost or 0.0),
                "capacity": edge.capacity,
                "score": edge.capacity / max(float(edge.construction_cost or 1.0), 1.0),
            }
            for edge in graph.get_all_edges(existing_only=False)
            if not edge.is_existing and edge.construction_cost is not None
        ),
        key=lambda item: item["score"],
        reverse=True,
    )[:3]

    total_distance = sum(edge.distance for edge in mst_edges)
    total_cost_estimate = sum(edge.distance * max(12 - edge.condition, 1) for edge in mst_edges)

    print(tabulate(
        [
            [edge.from_id, edge.to_id, round(edge.distance, 2), edge.condition, round(_mst_weight(edge), 3)]
            for edge in mst_edges
        ],
        headers=["From", "To", "Distance (km)", "Condition", "Weight"],
        tablefmt="grid",
    ))
    print(f"Mandatory edges included: {', '.join(f'{edge.from_id}-{edge.to_id}' for edge in mandatory_edges) or 'None'}")
    print(f"Total MST distance: {total_distance:.2f} km")
    print(f"Maintenance-oriented cost estimate: {total_cost_estimate:.2f}")
    print(tabulate(
        [[item["road"], item["distance_km"], item["capacity"], item["construction_cost"], round(item["score"], 3)] for item in suggestions],
        headers=["Suggested New Road", "Distance", "Capacity", "Cost (M EGP)", "Cost-Effectiveness"],
        tablefmt="grid",
    ))

    return MSTResult(mst_edges, total_distance, total_cost_estimate, mandatory_edges, suggestions)
