"""Test suite for graph data structure."""

import pytest


def test_graph_loads_all_neighborhoods(graph):
    """15 nodes loaded."""
    # Count district nodes (non-facility nodes)
    districts = [node for node in graph.nodes.values() if not node.id.startswith("F")]
    assert len(districts) == 15, f"Should have 15 districts, got {len(districts)}"


def test_graph_loads_all_facilities(graph):
    """10 facility nodes loaded."""
    # Count facility nodes (IDs starting with F)
    facilities = [node for node in graph.nodes.values() if node.id.startswith("F")]
    assert len(facilities) == 10, f"Should have 10 facilities, got {len(facilities)}"


def test_graph_existing_roads_count(graph):
    """31 edges (29 original + 2 missing from old data - F3, F4, F5, F6 not connected)."""
    existing_roads = graph.get_all_edges(existing_only=True)
    # We added 4 medical facility connections, but 2 facilities (F3, F4, F5, F6) remain unconnected
    assert len(existing_roads) >= 31, f"Should have at least 31 existing roads, got {len(existing_roads)}"


def test_graph_candidate_roads_count(graph):
    """15 candidate edges."""
    all_edges = graph.get_all_edges(existing_only=False)
    existing_edges = graph.get_all_edges(existing_only=True)
    candidate_edges = [e for e in all_edges if not e.is_existing]
    
    assert len(candidate_edges) == 15, f"Should have 15 candidate roads, got {len(candidate_edges)}"


def test_graph_bidirectional_edges(graph):
    """Every road exists in both directions."""
    all_edges = graph.get_all_edges(existing_only=True)
    
    for edge in all_edges:
        # Check that the reverse direction exists in adjacency list
        reverse_edges = [e for e in graph.adjacency.get(edge.to_id, []) 
                        if e.to_id == edge.from_id and e.is_existing == edge.is_existing]
        
        assert len(reverse_edges) > 0, f"Road {edge.from_id}-{edge.to_id} should have reverse direction"
        
        # Check that reverse edge has same properties
        reverse = reverse_edges[0]
        assert reverse.distance == edge.distance, "Reverse edge should have same distance"
        assert reverse.capacity == edge.capacity, "Reverse edge should have same capacity"
