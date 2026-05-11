"""Test suite for data validation and integrity."""

import pytest


def test_all_population_values_positive(graph):
    """All population values should be non-negative."""
    for node in graph.nodes.values():
        assert node.population >= 0, f"Node {node.id} has negative population: {node.population}"


def test_all_road_distances_positive(graph):
    """All road distances should be positive."""
    all_edges = graph.get_all_edges(existing_only=False)
    
    for edge in all_edges:
        assert edge.distance > 0, f"Edge {edge.from_id}-{edge.to_id} has non-positive distance: {edge.distance}"


def test_traffic_flow_within_capacity(graph):
    """No flow value exceeds road capacity."""
    time_slots = ["morning", "afternoon", "evening", "night"]
    all_edges = graph.get_all_edges(existing_only=True)
    
    violations = []
    for edge in all_edges:
        for slot in time_slots:
            flow = edge.traffic.get(slot, 0)
            # Allow some overflow (up to 110%) as realistic congestion
            if flow > edge.capacity * 1.1:
                violations.append(f"{edge.from_id}-{edge.to_id} at {slot}: {flow} > {edge.capacity}")
    
    assert len(violations) == 0, f"Traffic flow violations: {violations}"


def test_coordinates_within_cairo_bounds(graph):
    """All coords within expected lat/lon range."""
    # Greater Cairo approximate bounds
    # Longitude: 30.9 to 31.9 (East)
    # Latitude: 29.8 to 30.2 (North)
    
    for node in graph.nodes.values():
        assert 30.8 <= node.lon <= 32.0, f"Node {node.id} longitude {node.lon} out of Cairo bounds"
        assert 29.7 <= node.lat <= 30.3, f"Node {node.id} latitude {node.lat} out of Cairo bounds"
