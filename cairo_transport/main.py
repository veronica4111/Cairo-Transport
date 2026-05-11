"""Interactive CLI for the Cairo transport optimization system."""

from __future__ import annotations

from cairo_transport.algorithms.astar import astar_emergency
from cairo_transport.algorithms.dp_transit import (
    memoized_route_planner,
    optimize_bus_allocation,
    road_maintenance_allocation,
)
from cairo_transport.algorithms.greedy_signals import optimize_traffic_signals
from cairo_transport.algorithms.mst import modified_kruskal_mst
from cairo_transport.algorithms.shortest_path import dijkstra, route_to_airport
from cairo_transport.database import TransportDB
from cairo_transport.simulation import Scenario
from cairo_transport.utils import tabulate


def _load_visualization():
    """Load visualization functions lazily so the CLI can run without plotting deps."""
    try:
        from cairo_transport.visualization import draw_congestion_heatmap, draw_full_network, draw_mst, draw_shortest_path
    except ModuleNotFoundError as exc:
        print(f"Visualization dependency missing: {exc}. Install requirements.txt to enable plotting.")
        return None
    return draw_congestion_heatmap, draw_full_network, draw_mst, draw_shortest_path


def print_network_summary(graph) -> None:
    """Print high-level graph statistics."""
    node_rows = [[node.id, node.name, node.node_type, node.population] for node in graph.nodes.values()]
    print("\n[Network Summary]")
    print(f"Total nodes: {len(graph.nodes)}")
    print(f"Existing roads: {len(graph.get_all_edges(existing_only=True))}")
    print(tabulate(node_rows, headers=["ID", "Name", "Type", "Population"], tablefmt="grid"))


def print_db_summary(db: TransportDB) -> None:
    """Print database-level analytics and summary."""
    summary = db.network_summary()
    print("\n[Database Summary]")
    print(f"Database file: {db.db_path}")
    print(f"Total nodes: {summary['total_nodes']}")
    print(f"Existing roads: {summary['existing_roads']}")
    print(f"Candidate roads: {summary['candidate_roads']}")
    print(f"Metro lines: {summary['metro_lines']}")
    print(f"Bus routes: {summary['bus_routes']}")
    print(f"Total metro daily passengers: {summary['total_metro_daily']}")

    demand_pairs = db.top_demand_pairs(5)
    if demand_pairs:
        print("\nTop transport demand pairs:")
        demand_rows = [[row['from_name'], row['to_name'], row['daily_passengers']] for row in demand_pairs]
        print(tabulate(demand_rows, headers=["From", "To", "Daily Passengers"], tablefmt="grid"))


def run_all_scenarios(graph, db: TransportDB) -> None:
    """Run a full demo of the system."""
    visuals = _load_visualization()
    mst = modified_kruskal_mst(graph)
    Scenario.run_rush_hour(graph, "morning", db)
    Scenario.run_emergency(graph, "3")
    Scenario.run_road_closure(graph, "3", "10", db)
    Scenario.run_new_road_analysis(graph, db)
    optimize_bus_allocation(db.get_bus_routes(), 80)
    road_maintenance_allocation(graph.get_all_edges(existing_only=True), 350)
    optimize_traffic_signals(graph, "3", "morning")
    memoized_route_planner(graph, "3", ["5", "9", "5", "10", "9"], "morning")
    if visuals is not None:
        draw_congestion_heatmap, draw_full_network, draw_mst, _ = visuals
        draw_full_network(graph)
        draw_mst(graph, mst.edges, mst.mandatory_edges)
        draw_congestion_heatmap(graph, "morning")


def menu() -> None:
    """Run the interactive menu loop."""
    db = TransportDB()
    db.seed_from_data_module()
    graph = db.build_graph()
    while True:
        print(
            """
==== Smart City Transportation Network Optimization ====
1. View Network Summary
2. Find Shortest Route
3. Emergency Vehicle Routing
4. Run MST - Infrastructure Design
5. Optimize Bus Allocation
6. Road Maintenance Planner
7. Traffic Signal Optimizer
8. Simulate Rush Hour
9. Simulate Road Closure
10. Visualize Network
11. Run All Scenarios
12. Show Database Analytics
13. Show All Database Contents
14. Airport Access Route
0. Exit
"""
        )
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print_network_summary(graph)
        elif choice == "2":
            visuals = _load_visualization()
            source = input("Source node ID: ").strip()
            target = input("Target node ID: ").strip()
            time_of_day = input("Time of day [morning/afternoon/evening/night]: ").strip() or "morning"
            _, path, _ = dijkstra(graph, source, target, time_of_day)
            if path and visuals is not None:
                _, _, _, draw_shortest_path = visuals
                draw_shortest_path(graph, path, title=f"Shortest Path - {time_of_day.title()}")
        elif choice == "3":
            incident = input("Incident node ID: ").strip()
            astar_emergency(graph, incident)
        elif choice == "4":
            visuals = _load_visualization()
            result = modified_kruskal_mst(graph)
            if visuals is not None:
                _, _, draw_mst, _ = visuals
                draw_mst(graph, result.edges, result.mandatory_edges)
        elif choice == "5":
            budget = int(input("Enter total bus budget: ").strip())
            optimize_bus_allocation(db.get_bus_routes(), budget)
        elif choice == "6":
            budget = int(input("Enter maintenance budget (million EGP): ").strip())
            road_maintenance_allocation(graph.get_all_edges(existing_only=True), budget)
        elif choice == "7":
            intersection = input("Intersection node ID: ").strip()
            time_of_day = input("Time of day [morning/afternoon/evening/night]: ").strip() or "morning"
            optimize_traffic_signals(graph, intersection, time_of_day)
        elif choice == "8":
            time_of_day = input("Rush hour time [morning/afternoon/evening/night]: ").strip() or "morning"
            Scenario.run_rush_hour(graph, time_of_day, db)
        elif choice == "9":
            road_from = input("Closed road from node ID: ").strip()
            road_to = input("Closed road to node ID: ").strip()
            Scenario.run_road_closure(graph, road_from, road_to, db)
        elif choice == "10":
            visuals = _load_visualization()
            if visuals is not None:
                draw_congestion_heatmap, draw_full_network, _, _ = visuals
                draw_full_network(graph)
                draw_congestion_heatmap(graph, "morning")
        elif choice == "11":
            run_all_scenarios(graph, db)
        elif choice == "12":
            print_db_summary(db)
        elif choice == "13":
            db.print_all_contents()
        elif choice == "14":
            source = input("Source node ID: ").strip()
            time_of_day = input("Time of day [morning/afternoon/evening/night]: ").strip() or "morning"
            route_to_airport(graph, source, time_of_day)
        elif choice == "0":
            print("Exiting Smart City Transportation Network Optimization System.")
            db.close()
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    menu()
