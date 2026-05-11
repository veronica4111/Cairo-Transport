"""Test suite for database operations."""

import pytest


def test_db_connection(db):
    """SQLite connects without error."""
    assert db.con is not None, "Database connection should exist"
    # Try a simple query
    result = db.con.execute("SELECT 1").fetchone()
    assert result[0] == 1, "Database should be queryable"


def test_db_traffic_flow_loaded(db):
    """All time-slot records present."""
    # Check that traffic flows exist for all time slots
    time_slots = ["morning", "afternoon", "evening", "night"]
    
    for slot in time_slots:
        rows = db.con.execute(
            "SELECT COUNT(*) FROM traffic_flows WHERE time_slot = ?", (slot,)
        ).fetchone()
        count = rows[0]
        assert count > 0, f"Should have traffic flow records for {slot}"


def test_db_metro_lines_loaded(db):
    """3 metro lines in DB."""
    rows = db.con.execute("SELECT COUNT(*) FROM metro_lines").fetchone()
    count = rows[0]
    assert count == 3, f"Should have 3 metro lines, got {count}"


def test_db_bus_routes_loaded(db):
    """10 bus routes in DB."""
    routes = db.get_bus_routes()
    assert len(routes) == 10, f"Should have 10 bus routes, got {len(routes)}"
    
    # Check that each route has stops
    for route in routes:
        assert "stops" in route, f"Route {route['id']} should have stops"
        assert len(route["stops"]) > 0, f"Route {route['id']} should have at least one stop"
