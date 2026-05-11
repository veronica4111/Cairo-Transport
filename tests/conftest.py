"""Shared pytest fixtures for the Cairo transport test suite."""

import pytest
from cairo_transport.database import TransportDB
from cairo_transport.graph import TransportGraph


@pytest.fixture(scope="session")
def db():
    """Create a test database instance with seeded data."""
    test_db = TransportDB()
    test_db.seed_from_data_module()
    yield test_db
    test_db.close()


@pytest.fixture(scope="session")
def graph(db):
    """Build the transport graph from the test database."""
    return db.build_graph()


@pytest.fixture
def sample_nodes():
    """Return a list of sample node IDs for testing."""
    return ["1", "3", "5", "7", "10", "F1", "F9", "F10"]


@pytest.fixture
def medical_facilities():
    """Return medical facility node IDs."""
    return ["F9", "F10"]


@pytest.fixture
def mandatory_mst_nodes():
    """Return mandatory MST node IDs."""
    return ["F9", "F10", "13"]
