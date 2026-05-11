"""Graph data structures for the Cairo transportation project."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from cairo_transport.ml_congestion import predict_congestion, train_congestion_model


_ML_ARTIFACTS = train_congestion_model()
_ML_MODEL = _ML_ARTIFACTS.model if _ML_ARTIFACTS is not None else None


@dataclass(frozen=True)
class Node:
    """Represent a district or facility node in the transport network."""

    id: str
    name: str
    population: int
    node_type: str
    lon: float
    lat: float


@dataclass(frozen=True)
class Edge:
    """Represent a road edge with temporal traffic metadata."""

    from_id: str
    to_id: str
    distance: float
    capacity: int
    condition: int
    traffic: dict[str, int]
    is_existing: bool
    construction_cost: float | None = None

    @property
    def road_id(self) -> str:
        """Return a stable edge ID."""
        return f"{self.from_id}-{self.to_id}"

    def reversed_copy(self) -> "Edge":
        """Return the reverse-direction view of the same physical road."""
        return Edge(
            from_id=self.to_id,
            to_id=self.from_id,
            distance=self.distance,
            capacity=self.capacity,
            condition=self.condition,
            traffic=dict(self.traffic),
            is_existing=self.is_existing,
            construction_cost=self.construction_cost,
        )


class TransportGraph:
    """Store the transportation network as an adjacency list.

    Complexity:
    - add_node: O(1)
    - add_edge: O(1)
    - get_neighbors: O(deg(v))
    - get_euclidean_distance: O(1)
    """

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.adjacency: dict[str, list[Edge]] = {}
        self._undirected_edges: dict[frozenset[str], Edge] = {}

    def add_node(self, node_id: str, name: str, population: int, node_type: str, lon: float, lat: float) -> None:
        """Insert a node into the graph."""
        self.nodes[node_id] = Node(node_id, name, population, node_type, lon, lat)
        self.adjacency.setdefault(node_id, [])

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        distance: float,
        capacity: int,
        condition: int,
        traffic: dict[str, int],
        is_existing: bool,
        construction_cost: float | None,
    ) -> None:
        """Insert an undirected road by storing both directions."""
        edge = Edge(from_id, to_id, distance, capacity, condition, traffic, is_existing, construction_cost)
        self.adjacency.setdefault(from_id, []).append(edge)
        self.adjacency.setdefault(to_id, []).append(edge.reversed_copy())
        self._undirected_edges[frozenset((from_id, to_id))] = edge

    def get_neighbors(self, node_id: str, time_of_day: str, include_candidate: bool = False) -> list[tuple[Edge, float]]:
        """Return outgoing edges and congestion-aware weights for a node."""
        neighbors: list[tuple[Edge, float]] = []
        for edge in self.adjacency.get(node_id, []):
            if not include_candidate and not edge.is_existing:
                continue
            flow = edge.traffic.get(time_of_day, 0)
            predicted_congestion = predict_congestion(
                _ML_MODEL,
                time_of_day=time_of_day,
                flow=flow,
                capacity=edge.capacity,
                distance=edge.distance,
            )
            weight = edge.distance * (1 + predicted_congestion)
            neighbors.append((edge, weight))
        return neighbors

    def get_node(self, node_id: str) -> Node:
        """Return a node by ID."""
        return self.nodes[node_id]

    def get_euclidean_distance(self, id1: str, id2: str) -> float:
        """Return straight-line heuristic distance in kilometers."""
        node1 = self.nodes[id1]
        node2 = self.nodes[id2]
        return sqrt((node1.lon - node2.lon) ** 2 + (node1.lat - node2.lat) ** 2) * 111.0

    def get_all_edges(self, existing_only: bool = False) -> list[Edge]:
        """Return the unique undirected road list."""
        edges = list(self._undirected_edges.values())
        if existing_only:
            return [edge for edge in edges if edge.is_existing]
        return edges

    def get_incoming_edges(self, node_id: str, existing_only: bool = True) -> list[Edge]:
        """Return incoming edges to a node in the undirected graph."""
        incoming: list[Edge] = []
        for edge in self.get_all_edges(existing_only=existing_only):
            if edge.from_id == node_id:
                incoming.append(edge.reversed_copy())
            elif edge.to_id == node_id:
                incoming.append(edge)
        return incoming

    def has_edge(self, from_id: str, to_id: str) -> bool:
        """Check if an undirected road exists between two nodes."""
        return frozenset((from_id, to_id)) in self._undirected_edges

    def get_edge(self, from_id: str, to_id: str) -> Edge | None:
        """Return an undirected road if it exists."""
        edge = self._undirected_edges.get(frozenset((from_id, to_id)))
        if edge is None:
            return None
        if edge.from_id == from_id and edge.to_id == to_id:
            return edge
        return edge.reversed_copy()
