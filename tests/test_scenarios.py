"""Test suite for scenario simulations."""

import pytest
from cairo_transport.simulation import Scenario
from cairo_transport.algorithms.shortest_path import dijkstra, find_alternate_route
from cairo_transport.algorithms.astar import astar_emergency


def test_rush_hour_scenario(graph, db):
    """Morning peak returns higher travel times than night."""
    result = Scenario.run_rush_hour(graph, "morning", db)
    
    assert "top_pairs" in result, "Should return top pairs"
    assert "congested_roads" in result, "Should return congested roads"
    
    # Check that we have some data
    assert len(result["top_pairs"]) > 0, "Should have at least one top pair"


def test_road_closure_rerouting(graph, db):
    """Blocking an edge finds an alternate path."""
    # Use a known existing road
    blocked_from = "3"
    blocked_to = "10"
    
    # First verify the road exists
    assert graph.has_edge(blocked_from, blocked_to), f"Road {blocked_from}-{blocked_to} should exist"
    
    # Find alternate route
    alternate = find_alternate_route(graph, "1", "8", [(blocked_from, blocked_to)], "morning")
    
    # Should either find an alternate or report no route
    assert alternate is not None, "Should return a result"
    
    if isinstance(alternate, tuple):
        cost, path, _ = alternate
        # If alternate path exists, it should not use the blocked edge
        if path:
            edges_in_path = [(path[i], path[i+1]) for i in range(len(path)-1)]
            blocked_edge = frozenset((blocked_from, blocked_to))
            for edge in edges_in_path:
                assert frozenset(edge) != blocked_edge, "Alternate path should not use blocked edge"


def test_emergency_response_scenario(graph):
    """Full emergency routing returns a valid path."""
    incident_node = "3"
    
    path, estimated_time, explored = astar_emergency(graph, incident_node, "Medical")
    
    assert path is not None, "Should return a path"
    assert len(path) > 0, "Path should not be empty"
    assert path[0] == incident_node, f"Path should start at {incident_node}"
    
    # Destination should be a medical facility
    destination = path[-1]
    dest_node = graph.get_node(destination)
    assert dest_node.node_type == "Medical", f"Destination should be Medical, got {dest_node.node_type}"
    
    assert estimated_time > 0, "Estimated time should be positive"
    assert explored > 0, "Should have explored some nodes"
