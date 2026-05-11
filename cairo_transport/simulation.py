"""Scenario simulation runner for the transport management system."""

from __future__ import annotations

from cairo_transport.algorithms.astar import astar_emergency
from cairo_transport.algorithms.greedy_signals import emergency_preemption
from cairo_transport.algorithms.mst import modified_kruskal_mst
from cairo_transport.algorithms.shortest_path import dijkstra, find_alternate_route, time_aware_dijkstra
from cairo_transport.database import TransportDB
from cairo_transport.graph import TransportGraph
from cairo_transport.utils import tabulate


class Scenario:
    """Run repeatable analysis scenarios for demos and evaluation."""

    @staticmethod
    def run_rush_hour(graph: TransportGraph, time: str = "morning", db: TransportDB | None = None) -> dict[str, object]:
        """Simulate rush-hour routing for top demand pairs."""

        print(f"\n[Scenario] Rush hour simulation at {time}")
        top_pairs = db.get_transport_demand(5) if db is not None else []
        if not top_pairs:
            raise ValueError("No transport demand data available. Ensure the database is seeded before running scenarios.")
        
        # Get metro lines for rush hour optimization
        metro_lines = []
        if db is not None:
            metro_rows = db.con.execute("SELECT * FROM metro_lines").fetchall()
            for metro in metro_rows:
                stations = [s["station_id"] for s in db.con.execute(
                    "SELECT station_id FROM metro_stations WHERE line_id=? ORDER BY seq",
                    (metro["id"],)
                ).fetchall()]
                metro_lines.append({"id": metro["id"], "name": metro["name"], "stations": stations})
        
        rows: list[list[object]] = []
        alternates: list[str] = []

        for pair in top_pairs:
            comparison = time_aware_dijkstra(graph, pair["from"], pair["to"], metro_lines=metro_lines)
            slot_data = comparison["results"][time]
            path = slot_data["path"]
            rows.append([pair["from"], pair["to"], pair["daily_passengers"], round(slot_data["cost"], 2), len(path)])
            if len(path) > 1:
                alternate = find_alternate_route(graph, pair["from"], pair["to"], [(path[0], path[1])], time)
                if isinstance(alternate, tuple) and alternate[1]:
                    alternates.append(
                        f"{graph.get_node(pair['from']).name} -> {graph.get_node(pair['to']).name}: "
                        + " -> ".join(graph.get_node(node).name for node in alternate[1])
                    )

        congested = []
        for edge in graph.get_all_edges(existing_only=True):
            ratio = edge.traffic.get(time, 0) / edge.capacity if edge.capacity else 0
            if ratio > 0.85:
                congested.append((f"{edge.from_id}-{edge.to_id}", round(ratio * 100, 1)))

        print(tabulate(rows, headers=["From", "To", "Demand", "Cost", "Stops"], tablefmt="grid"))
        print("Roads over 85% capacity:", ", ".join(f"{road} ({pct}%)" for road, pct in congested) or "None")
        print("Top alternate routes:")
        for route in alternates[:3]:
            print(f"  - {route}")
        return {"top_pairs": rows, "congested_roads": congested, "alternate_routes": alternates[:3]}

    @staticmethod
    def run_emergency(graph: TransportGraph, incident_location_id: str, hospital: str = "nearest") -> dict[str, object]:
        """Simulate medical emergency response and preemption."""

        print(f"\n[Scenario] Emergency from {graph.get_node(incident_location_id).name} to {hospital} hospital")
        path, estimated_time, explored = astar_emergency(graph, incident_location_id, target_facility_type="Medical")
        preemption, delay = emergency_preemption(graph, path, "morning") if path else ([], 0.0)
        normal_time = estimated_time * 1.5 if estimated_time else 0.0
        print(f"Normal response time estimate: {normal_time:.2f} minutes")
        print(f"Preempted response time estimate: {estimated_time:.2f} minutes")
        return {
            "path": path,
            "normal_time_minutes": normal_time,
            "preempted_time_minutes": estimated_time,
            "nodes_explored": explored,
            "preemption": preemption,
            "delay_to_others": delay,
        }

    @staticmethod
    def run_road_closure(
        graph: TransportGraph,
        closed_road_from: str,
        closed_road_to: str,
        db: TransportDB | None = None,
    ) -> dict[str, object]:
        """Measure the impact of a road closure on high-demand O-D pairs."""

        print(f"\n[Scenario] Road closure: {closed_road_from} <-> {closed_road_to}")
        impacted: list[list[object]] = []
        blocked = frozenset((closed_road_from, closed_road_to))
        pairs = db.get_transport_demand(8) if db is not None else []
        if not pairs:
            raise ValueError("No transport demand data available for road closure scenario.")
        for pair in pairs:
            base_cost, base_path, _ = dijkstra(graph, pair["from"], pair["to"], "morning")
            if blocked not in {frozenset((a, b)) for a, b in zip(base_path, base_path[1:])}:
                continue
            alternate = find_alternate_route(graph, pair["from"], pair["to"], [(closed_road_from, closed_road_to)], "morning")
            if isinstance(alternate, str):
                impacted.append([pair["from"], pair["to"], "No alternate route", "High"])
            else:
                alt_cost = alternate[0]
                impact = "High" if alt_cost > base_cost * 1.25 else "Medium"
                impacted.append([pair["from"], pair["to"], round(alt_cost - base_cost, 2), impact])

        print(tabulate(impacted, headers=["From", "To", "Extra Cost / Status", "Impact"], tablefmt="grid"))
        return {"impacted_routes": impacted}

    @staticmethod
    def run_new_road_analysis(graph: TransportGraph, db: TransportDB | None = None) -> dict[str, object]:
        """Analyze MST suggestions and candidate-road impact."""

        print("\n[Scenario] New road infrastructure analysis")
        mst = modified_kruskal_mst(graph)
        projected = []

        if db is not None:
            candidate_rows = db.get_candidate_roads()
            print("[Scenario] Using candidate road data from database")
            for row in candidate_rows:
                road = f"{row['from_id']} <-> {row['to_id']}"
                score = float(row['capacity']) / max(float(row['construction_cost'] or 1.0), 1.0)
                projected.append([road, round(score, 3), round(float(row['capacity']) / 100.0, 2)])
        else:
            for item in mst.suggested_new_roads:
                projected_reduction = round(float(item["capacity"]) / 100.0, 2)
                projected.append([item["road"], round(float(item["score"]), 3), projected_reduction])

        print(tabulate(projected, headers=["Candidate", "Cost-Effectiveness", "Projected Congestion Reduction %"], tablefmt="grid"))
        return {"mst": mst, "projected_reduction": projected}
