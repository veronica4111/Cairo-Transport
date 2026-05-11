
"""
SQLite database layer for the Cairo Transportation project.

Replaces the hardcoded lists in data.py with a proper relational database.
The DB is a single file (cairo_transport.db) — no server required.

Usage
-----
    from database import TransportDB

    db = TransportDB()                  # creates / opens the DB file
    db.seed_from_data_module()          # populate once from the old data.py lists
    graph = db.build_graph()            # same TransportGraph you had before

    # --- example queries ---
    db.get_node("3")
    db.get_congested_roads("morning", threshold=0.85)
    db.get_roads_by_condition(max_condition=6)
    db.update_traffic("1-3", "morning", 2950)
    db.add_candidate_road("1","13", distance_km=55.0, capacity=4200, cost=1050)
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from .utils import tabulate

# ---------------------------------------------------------------------------
# Re-import the old static data so we can seed the DB once
# ---------------------------------------------------------------------------
from .data import (
    BUS_ROUTES,
    CANDIDATE_ROADS,
    DISTRICTS,
    EXISTING_ROADS,
    FACILITIES,
    METRO_LINES,
    PUBLIC_TRANSPORT_DEMAND,
    TIME_SLOTS,
    TRAFFIC_FLOWS,
    traffic_lookup,
)
from .graph import TransportGraph

DB_PATH = Path(os.environ.get("CAIRO_TRANSPORT_DB_PATH", Path(__file__).parent / "cairo_transport.db"))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS nodes (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    population  INTEGER NOT NULL DEFAULT 0,
    node_type   TEXT NOT NULL,
    lon         REAL NOT NULL,
    lat         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS roads (
    id              TEXT PRIMARY KEY,        -- e.g. "1-3"
    from_id         TEXT NOT NULL REFERENCES nodes(id),
    to_id           TEXT NOT NULL REFERENCES nodes(id),
    distance_km     REAL NOT NULL,
    capacity        INTEGER NOT NULL,
    condition       INTEGER NOT NULL CHECK(condition BETWEEN 1 AND 10),
    is_existing     INTEGER NOT NULL DEFAULT 1,   -- 1 = existing, 0 = candidate
    construction_cost REAL,                       -- NULL for existing roads
    UNIQUE(from_id, to_id)
);

CREATE TABLE IF NOT EXISTS traffic_flows (
    road_id     TEXT NOT NULL REFERENCES roads(id),
    time_slot   TEXT NOT NULL CHECK(time_slot IN ('morning','afternoon','evening','night')),
    flow        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (road_id, time_slot)
);

CREATE TABLE IF NOT EXISTS metro_lines (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    daily_passengers INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metro_stations (
    line_id     TEXT NOT NULL REFERENCES metro_lines(id),
    station_id  TEXT NOT NULL REFERENCES nodes(id),
    seq         INTEGER NOT NULL,
    PRIMARY KEY (line_id, station_id)
);

CREATE TABLE IF NOT EXISTS bus_routes (
    id              TEXT PRIMARY KEY,
    buses_assigned  INTEGER NOT NULL,
    daily_passengers INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bus_stops (
    route_id    TEXT NOT NULL REFERENCES bus_routes(id),
    node_id     TEXT NOT NULL REFERENCES nodes(id),
    seq         INTEGER NOT NULL,
    PRIMARY KEY (route_id, node_id, seq)
);

CREATE TABLE IF NOT EXISTS transport_demand (
    from_id         TEXT NOT NULL REFERENCES nodes(id),
    to_id           TEXT NOT NULL REFERENCES nodes(id),
    daily_passengers INTEGER NOT NULL,
    PRIMARY KEY (from_id, to_id)
);
"""

# ---------------------------------------------------------------------------
# Main DB class
# ---------------------------------------------------------------------------

class TransportDB:
    """Thin wrapper around a SQLite connection."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row          # rows behave like dicts
        self.con.execute("PRAGMA foreign_keys = ON")
        self._apply_schema()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _apply_schema(self) -> None:
        self.con.executescript(_SCHEMA)
        self.con.commit()

    def seed_from_data_module(self, force: bool = False) -> None:
        """Populate the DB from the original data.py lists (run once).

        Set force=True to wipe and re-seed.
        """
        if force:
            self.con.executescript("""
                DELETE FROM transport_demand;
                DELETE FROM bus_stops;
                DELETE FROM bus_routes;
                DELETE FROM metro_stations;
                DELETE FROM metro_lines;
                DELETE FROM traffic_flows;
                DELETE FROM roads;
                DELETE FROM nodes;
            """)
            self.con.commit()

        # Skip if already seeded
        if self.con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] > 0:
            print("[DB] Already seeded — skipping. Pass force=True to re-seed.")
            return

        cur = self.con

        # nodes
        for d in DISTRICTS:
            cur.execute(
                "INSERT OR IGNORE INTO nodes VALUES (?,?,?,?,?,?)",
                (d["id"], d["name"], d["population"], d["type"], d["x"], d["y"]),
            )
        for f in FACILITIES:
            cur.execute(
                "INSERT OR IGNORE INTO nodes VALUES (?,?,?,?,?,?)",
                (f["id"], f["name"], 0, f["type"], f["x"], f["y"]),
            )

        traffic = traffic_lookup()

        # existing roads
        for r in EXISTING_ROADS:
            road_id = f"{r['from']}-{r['to']}"
            cur.execute(
                "INSERT OR IGNORE INTO roads VALUES (?,?,?,?,?,?,1,NULL)",
                (road_id, r["from"], r["to"], r["distance_km"], r["capacity"], r["condition"]),
            )
            for slot in TIME_SLOTS:
                flow = traffic.get(road_id, {}).get(slot, 0)
                cur.execute(
                    "INSERT OR IGNORE INTO traffic_flows VALUES (?,?,?)",
                    (road_id, slot, flow),
                )

        # candidate roads
        for r in CANDIDATE_ROADS:
            road_id = f"{r['from']}-{r['to']}"
            cur.execute(
                "INSERT OR IGNORE INTO roads VALUES (?,?,?,?,?,8,0,?)",
                (road_id, r["from"], r["to"], r["distance_km"], r["capacity"], r["construction_cost"]),
            )
            for slot in TIME_SLOTS:
                cur.execute(
                    "INSERT OR IGNORE INTO traffic_flows VALUES (?,?,0)",
                    (road_id, slot),
                )

        # metro
        for line in METRO_LINES:
            cur.execute(
                "INSERT OR IGNORE INTO metro_lines VALUES (?,?,?)",
                (line["id"], line["name"], line["daily_passengers"]),
            )
            for seq, station in enumerate(line["stations"]):
                cur.execute(
                    "INSERT OR IGNORE INTO metro_stations VALUES (?,?,?)",
                    (line["id"], station, seq),
                )

        # bus
        for route in BUS_ROUTES:
            cur.execute(
                "INSERT OR IGNORE INTO bus_routes VALUES (?,?,?)",
                (route["id"], route["buses_assigned"], route["daily_passengers"]),
            )
            for seq, stop in enumerate(route["stops"]):
                cur.execute(
                    "INSERT OR IGNORE INTO bus_stops VALUES (?,?,?)",
                    (route["id"], stop, seq),
                )

        # demand
        for d in PUBLIC_TRANSPORT_DEMAND:
            cur.execute(
                "INSERT OR IGNORE INTO transport_demand VALUES (?,?,?)",
                (d["from"], d["to"], d["daily_passengers"]),
            )

        self.con.commit()
        print(f"[DB] Seeded successfully → {self.db_path}")

    # ------------------------------------------------------------------
    # Node queries
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> sqlite3.Row | None:
        return self.con.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()

    def get_all_nodes(self) -> list[sqlite3.Row]:
        return self.con.execute("SELECT * FROM nodes ORDER BY id").fetchall()

    def get_nodes_by_type(self, node_type: str) -> list[sqlite3.Row]:
        return self.con.execute("SELECT * FROM nodes WHERE node_type=?", (node_type,)).fetchall()

    # ------------------------------------------------------------------
    # Road queries
    # ------------------------------------------------------------------

    def get_road(self, from_id: str, to_id: str) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM roads WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
            (from_id, to_id, to_id, from_id),
        ).fetchone()

    def get_all_roads(self, existing_only: bool = False) -> list[sqlite3.Row]:
        if existing_only:
            return self.con.execute("SELECT * FROM roads WHERE is_existing=1").fetchall()
        return self.con.execute("SELECT * FROM roads").fetchall()

    def get_roads_by_condition(self, max_condition: int = 6) -> list[sqlite3.Row]:
        """Return roads needing maintenance (condition ≤ threshold)."""
        return self.con.execute(
            "SELECT * FROM roads WHERE condition <= ? AND is_existing=1 ORDER BY condition",
            (max_condition,),
        ).fetchall()

    def get_candidate_roads(self) -> list[sqlite3.Row]:
        return self.con.execute("SELECT * FROM roads WHERE is_existing=0 ORDER BY construction_cost").fetchall()

    def get_bus_routes(self) -> list[dict[str, Any]]:
        rows = self.con.execute("SELECT id, buses_assigned, daily_passengers FROM bus_routes ORDER BY id").fetchall()
        routes: list[dict[str, Any]] = []
        for row in rows:
            stops = [stop["node_id"] for stop in self.con.execute(
                "SELECT node_id FROM bus_stops WHERE route_id=? ORDER BY seq",
                (row["id"],),
            ).fetchall()]
            routes.append(
                {
                    "id": row["id"],
                    "buses_assigned": int(row["buses_assigned"]),
                    "daily_passengers": int(row["daily_passengers"]),
                    "stops": stops,
                }
            )
        return routes

    def get_transport_demand(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT from_id, to_id, daily_passengers FROM transport_demand ORDER BY daily_passengers DESC"
        if limit is not None:
            rows = self.con.execute(f"{query} LIMIT ?", (limit,)).fetchall()
        else:
            rows = self.con.execute(query).fetchall()
        return [{"from": row["from_id"], "to": row["to_id"], "daily_passengers": row["daily_passengers"]} for row in rows]

    # ------------------------------------------------------------------
    # Traffic queries
    # ------------------------------------------------------------------

    def get_traffic(self, road_id: str, time_slot: str) -> int:
        row = self.con.execute(
            "SELECT flow FROM traffic_flows WHERE road_id=? AND time_slot=?",
            (road_id, time_slot),
        ).fetchone()
        return int(row["flow"]) if row else 0

    def get_all_traffic_for_road(self, road_id: str) -> dict[str, int]:
        rows = self.con.execute(
            "SELECT time_slot, flow FROM traffic_flows WHERE road_id=?", (road_id,)
        ).fetchall()
        return {r["time_slot"]: r["flow"] for r in rows}

    def get_congested_roads(self, time_slot: str, threshold: float = 0.85) -> list[dict[str, Any]]:
        """Return roads where flow/capacity exceeds threshold at a given time."""
        rows = self.con.execute("""
            SELECT r.id, r.from_id, r.to_id, r.capacity, t.flow,
                   CAST(t.flow AS REAL) / r.capacity AS ratio
            FROM roads r
            JOIN traffic_flows t ON t.road_id = r.id
            WHERE t.time_slot = ?
              AND r.capacity > 0
              AND CAST(t.flow AS REAL) / r.capacity > ?
            ORDER BY ratio DESC
        """, (time_slot, threshold)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def update_traffic(self, road_id: str, time_slot: str, new_flow: int) -> None:
        self.con.execute(
            "UPDATE traffic_flows SET flow=? WHERE road_id=? AND time_slot=?",
            (new_flow, road_id, time_slot),
        )
        self.con.commit()

    def update_road_condition(self, road_id: str, new_condition: int) -> None:
        self.con.execute(
            "UPDATE roads SET condition=? WHERE id=?", (new_condition, road_id)
        )
        self.con.commit()

    def add_candidate_road(
        self,
        from_id: str,
        to_id: str,
        distance_km: float,
        capacity: int,
        cost: float,
    ) -> None:
        road_id = f"{from_id}-{to_id}"
        self.con.execute(
            "INSERT OR REPLACE INTO roads VALUES (?,?,?,?,?,8,0,?)",
            (road_id, from_id, to_id, distance_km, capacity, cost),
        )
        for slot in TIME_SLOTS:
            self.con.execute(
                "INSERT OR IGNORE INTO traffic_flows VALUES (?,?,0)", (road_id, slot)
            )
        self.con.commit()
        print(f"[DB] Added candidate road {road_id}")

    # ------------------------------------------------------------------
    # Build TransportGraph (drop-in replacement for build_graph())
    # ------------------------------------------------------------------

    def build_graph(self) -> TransportGraph:
        """Build the same TransportGraph your algorithms expect, now from the DB."""
        graph = TransportGraph()

        for node in self.get_all_nodes():
            graph.add_node(node["id"], node["name"], node["population"],
                           node["node_type"], node["lon"], node["lat"])

        for road in self.get_all_roads():
            traffic = self.get_all_traffic_for_road(road["id"])
            graph.add_edge(
                from_id=road["from_id"],
                to_id=road["to_id"],
                distance=road["distance_km"],
                capacity=road["capacity"],
                condition=road["condition"],
                traffic=traffic,
                is_existing=bool(road["is_existing"]),
                construction_cost=road["construction_cost"],
            )

        return graph

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------

    def top_demand_pairs(self, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.con.execute("""
            SELECT td.from_id, n1.name as from_name,
                   td.to_id,   n2.name as to_name,
                   td.daily_passengers
            FROM transport_demand td
            JOIN nodes n1 ON n1.id = td.from_id
            JOIN nodes n2 ON n2.id = td.to_id
            ORDER BY td.daily_passengers DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def network_summary(self) -> dict[str, Any]:
        return {
            "total_nodes":       self.con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0],
            "existing_roads":    self.con.execute("SELECT COUNT(*) FROM roads WHERE is_existing=1").fetchone()[0],
            "candidate_roads":   self.con.execute("SELECT COUNT(*) FROM roads WHERE is_existing=0").fetchone()[0],
            "metro_lines":       self.con.execute("SELECT COUNT(*) FROM metro_lines").fetchone()[0],
            "bus_routes":        self.con.execute("SELECT COUNT(*) FROM bus_routes").fetchone()[0],
            "total_metro_daily": self.con.execute("SELECT SUM(daily_passengers) FROM metro_lines").fetchone()[0],
        }

    def print_all_contents(self) -> None:
        """Print all database contents in a formatted way."""
        print("\n" + "=" * 70)
        print("DATABASE CONTENTS")
        print("=" * 70)

        # Nodes
        print("\n[Nodes]")
        nodes = self.get_all_nodes()
        node_rows = [[n["id"], n["name"], n["node_type"], n["population"]] for n in nodes]
        print(tabulate(node_rows, headers=["ID", "Name", "Type", "Population"], tablefmt="grid"))

        # Existing Roads
        print("\n[Existing Roads]")
        roads = self.get_all_roads(existing_only=True)
        road_rows = [[r["id"], r["from_id"], r["to_id"], r["distance_km"], r["capacity"], r["condition"]] for r in roads]
        print(tabulate(road_rows, headers=["ID", "From", "To", "Distance", "Capacity", "Condition"], tablefmt="grid"))

        # Candidate Roads
        print("\n[Candidate Roads]")
        cand_roads = self.get_candidate_roads()
        cand_rows = [[r["id"], r["from_id"], r["to_id"], r["distance_km"], r["capacity"], r["construction_cost"]] for r in cand_roads]
        print(tabulate(cand_rows, headers=["ID", "From", "To", "Distance", "Capacity", "Cost"], tablefmt="grid"))

        # Bus Routes
        print("\n[Bus Routes]")
        bus_routes = self.get_bus_routes()
        bus_rows = [[b["id"], b["buses_assigned"], b["daily_passengers"], " -> ".join(b["stops"])] for b in bus_routes]
        print(tabulate(bus_rows, headers=["ID", "Buses", "Passengers", "Stops"], tablefmt="grid"))

        # Transport Demand
        print("\n[Transport Demand]")
        demand = self.get_transport_demand()
        demand_rows = [[d["from"], d["to"], d["daily_passengers"]] for d in demand]
        print(tabulate(demand_rows, headers=["From", "To", "Daily Passengers"], tablefmt="grid"))

        # Traffic Flows (sample)
        print("\n[Traffic Flows - Sample]")
        sample_roads = self.get_all_roads(existing_only=True)[:5]
        for r in sample_roads:
            traffic = self.get_all_traffic_for_road(r["id"])
            print(f"  {r['id']}: {traffic}")

        # Metro Lines
        print("\n[Metro Lines]")
        metro_lines = self.con.execute("SELECT * FROM metro_lines").fetchall()
        if metro_lines:
            metro_rows = [[m["id"], m["name"], m["daily_passengers"]] for m in metro_lines]
            print(tabulate(metro_rows, headers=["ID", "Name", "Daily Passengers"], tablefmt="grid"))
        else:
            print("  (none)")

        print("\n" + "=" * 70)

    def close(self) -> None:
        self.con.close()
