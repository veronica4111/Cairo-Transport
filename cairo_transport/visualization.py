"""Visualization helpers for the Cairo transport graph."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from cairo_transport.graph import Edge, TransportGraph

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

NODE_COLORS = {
    "Residential": "royalblue",
    "Business": "firebrick",
    "Mixed": "seagreen",
    "Industrial": "gray",
    "Government": "gold",
    "Airport": "purple",
    "Transport Hub": "purple",
    "Education": "purple",
    "Tourism": "purple",
    "Sports": "purple",
    "Commercial": "purple",
    "Medical": "purple",
}


def _build_nx_graph(graph: TransportGraph) -> nx.Graph:
    """Convert the custom graph into a NetworkX graph."""
    nx_graph = nx.Graph()
    for node in graph.nodes.values():
        nx_graph.add_node(node.id, label=node.name, pos=(node.lon, node.lat), population=node.population, node_type=node.node_type)
    for edge in graph.get_all_edges(existing_only=True):
        nx_graph.add_edge(edge.from_id, edge.to_id, capacity=edge.capacity, distance=edge.distance, condition=edge.condition)
    return nx_graph


def _node_sizes(graph: TransportGraph) -> list[float]:
    """Return population-scaled node sizes."""
    sizes = []
    for node in graph.nodes.values():
        if node.population == 0:
            sizes.append(350)
        else:
            sizes.append(max(250, node.population / 1200))
    return sizes


def draw_full_network(graph: TransportGraph) -> Path:
    """Draw and save the full transportation network."""
    nx_graph = _build_nx_graph(graph)
    positions = nx.get_node_attributes(nx_graph, "pos")
    colors = [NODE_COLORS.get(graph.get_node(node_id).node_type, "black") for node_id in nx_graph.nodes]
    widths = [max(1.0, data["capacity"] / 1000.0) for _, _, data in nx_graph.edges(data=True)]

    plt.figure(figsize=(14, 10))
    nx.draw(nx_graph, positions, with_labels=False, node_color=colors, node_size=_node_sizes(graph), width=widths, edge_color="slategray")
    nx.draw_networkx_labels(nx_graph, positions, labels={node.id: node.name for node in graph.nodes.values()}, font_size=8)
    plt.title("Greater Cairo Transportation Network")
    output_path = OUTPUT_DIR / "full_network.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.show()
    plt.close()
    return output_path


def draw_mst(graph: TransportGraph, mst_edges: list[Edge], mandatory_edges: list[Edge]) -> Path:
    """Draw and save the MST overlay."""
    nx_graph = _build_nx_graph(graph)
    positions = nx.get_node_attributes(nx_graph, "pos")
    plt.figure(figsize=(14, 10))
    nx.draw(nx_graph, positions, with_labels=False, node_color="lightgray", node_size=_node_sizes(graph), edge_color="lightgray")
    nx.draw_networkx_labels(nx_graph, positions, labels={node.id: node.name for node in graph.nodes.values()}, font_size=8)
    nx.draw_networkx_edges(nx_graph, positions, edgelist=[(edge.from_id, edge.to_id) for edge in mst_edges], edge_color="green", width=3)
    nx.draw_networkx_edges(nx_graph, positions, edgelist=[(edge.from_id, edge.to_id) for edge in mandatory_edges], edge_color="red", width=4)
    plt.title("Modified Kruskal MST Overlay")
    output_path = OUTPUT_DIR / "mst_overlay.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.show()
    plt.close()
    return output_path


def draw_shortest_path(graph: TransportGraph, path: list[str], title: str = "Shortest Path") -> Path:
    """Draw and save a highlighted route."""
    nx_graph = _build_nx_graph(graph)
    positions = nx.get_node_attributes(nx_graph, "pos")
    highlighted = list(zip(path, path[1:]))

    plt.figure(figsize=(14, 10))
    nx.draw(nx_graph, positions, with_labels=False, node_color="lightgray", node_size=_node_sizes(graph), edge_color="silver")
    nx.draw_networkx_labels(nx_graph, positions, labels={node.id: node.name for node in graph.nodes.values()}, font_size=8)
    nx.draw_networkx_edges(nx_graph, positions, edgelist=highlighted, edge_color="orange", width=4, arrows=True)
    plt.title(title)
    output_path = OUTPUT_DIR / "shortest_path.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.show()
    plt.close()
    return output_path


def draw_congestion_heatmap(graph: TransportGraph, time_of_day: str) -> Path:
    """Draw and save a congestion heatmap for a given time slot."""
    nx_graph = _build_nx_graph(graph)
    positions = nx.get_node_attributes(nx_graph, "pos")
    edge_colors = []

    for start, end in nx_graph.edges:
        edge = graph.get_edge(start, end)
        ratio = edge.traffic.get(time_of_day, 0) / edge.capacity if edge and edge.capacity else 0
        if ratio < 0.6:
            edge_colors.append("green")
        elif ratio <= 0.85:
            edge_colors.append("gold")
        else:
            edge_colors.append("red")

    plt.figure(figsize=(14, 10))
    nx.draw(nx_graph, positions, with_labels=False, node_color="lightgray", node_size=_node_sizes(graph), edge_color=edge_colors, width=3)
    nx.draw_networkx_labels(nx_graph, positions, labels={node.id: node.name for node in graph.nodes.values()}, font_size=8)
    plt.title(f"Congestion Heatmap - {time_of_day.title()}")
    output_path = OUTPUT_DIR / f"congestion_{time_of_day}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.show()
    plt.close()
    return output_path
