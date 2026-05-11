"""FastAPI backend for the Cairo Smart City Transportation Network Optimization system.

Exposes every CLI feature as a REST endpoint, using the real algorithm functions.
"""

from __future__ import annotations

import sys
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the project root is on sys.path so cairo_transport resolves
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cairo_transport.database import TransportDB
from cairo_transport.graph import TransportGraph
from cairo_transport.data import TRAFFIC_FLOWS, EXISTING_ROADS, CANDIDATE_ROADS, DISTRICTS, FACILITIES
from cairo_transport.algorithms.shortest_path import dijkstra, find_alternate_route, time_aware_dijkstra, route_to_airport
from cairo_transport.algorithms.astar import astar_emergency
from cairo_transport.algorithms.mst import modified_kruskal_mst
from cairo_transport.algorithms.dp_transit import (
    optimize_bus_allocation,
    road_maintenance_allocation,
    memoized_route_planner,
)
from cairo_transport.algorithms.greedy_signals import optimize_traffic_signals
from cairo_transport.simulation import Scenario
from cairo_transport.ml_congestion import predict_congestion, train_congestion_model
from cairo_transport.visual_runners import run_visual_trace

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
db: TransportDB | None = None
graph: TransportGraph | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, graph
    import sqlite3
    from cairo_transport.database import DB_PATH
    # Create DB with check_same_thread=False so FastAPI threadpool can access it
    db = TransportDB.__new__(TransportDB)
    db.db_path = DB_PATH
    db.con = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.con.row_factory = sqlite3.Row
    db.con.execute("PRAGMA foreign_keys = ON")
    db._apply_schema()
    db.seed_from_data_module()
    graph = db.build_graph()
    yield
    if db is not None:
        db.close()


app = FastAPI(title="Cairo Transport API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ShortestPathRequest(BaseModel):
    source: str
    target: str
    time_of_day: str = "morning"


class EmergencyRequest(BaseModel):
    incident_node: str


class BusAllocationRequest(BaseModel):
    budget: int


class RoadMaintenanceRequest(BaseModel):
    budget: int


class TrafficSignalsRequest(BaseModel):
    node_id: str
    time_of_day: str = "morning"


class MemoizedPlannerRequest(BaseModel):
    source: str
    destinations: list[str]
    time_of_day: str = "morning"


class AirportAccessRequest(BaseModel):
    source: str
    time_of_day: str = "morning"


class RushHourRequest(BaseModel):
    time_of_day: str = "morning"


class RoadClosureRequest(BaseModel):
    from_node: str
    to_node: str


class CongestionPredictionRequest(BaseModel):
    time_of_day: str = "morning"
    flow: float
    capacity: float
    distance: float


class AlgorithmRaceRequest(BaseModel):
    algorithm_a: str = "dijkstra"
    algorithm_b: str = "astar"
    source: str
    target: str
    time_of_day: str = "morning"


# ---------------------------------------------------------------------------
# Network endpoints
# ---------------------------------------------------------------------------
@app.get("/api/network/summary")
def network_summary():
    """High-level graph statistics."""
    assert graph is not None
    nodes = list(graph.nodes.values())
    existing_edges = graph.get_all_edges(existing_only=True)
    all_edges = graph.get_all_edges()

    # Compute average morning congestion
    total_ratio = 0.0
    count = 0
    for edge in existing_edges:
        flow = edge.traffic.get("morning", 0)
        if edge.capacity > 0:
            total_ratio += flow / edge.capacity
            count += 1
    avg_congestion = round(total_ratio / count, 4) if count > 0 else 0

    # Network coverage: nodes with at least one existing edge / total nodes
    connected_nodes = set()
    for edge in existing_edges:
        connected_nodes.add(edge.from_id)
        connected_nodes.add(edge.to_id)
    coverage = round(len(connected_nodes) / len(nodes), 4) if nodes else 0

    return {
        "total_nodes": len(nodes),
        "total_edges": len(all_edges),
        "existing_edges": len(existing_edges),
        "candidate_edges": len(all_edges) - len(existing_edges),
        "avg_congestion": avg_congestion,
        "network_coverage": coverage,
        "active_assets": len(nodes) + len(all_edges),
    }


@app.get("/api/network/nodes")
def network_nodes():
    """Return all nodes with their full data."""
    assert graph is not None
    result = []
    for node in graph.nodes.values():
        # Count connected existing edges
        connected_roads = len([e for e in graph.adjacency.get(node.id, []) if e.is_existing])
        result.append({
            "id": node.id,
            "name": node.name,
            "population": node.population,
            "node_type": node.node_type,
            "lon": node.lon,
            "lat": node.lat,
            "connected_roads": connected_roads,
        })
    return result


@app.get("/api/network/edges")
def network_edges():
    """Return all edges with traffic data."""
    assert graph is not None
    result = []
    for edge in graph.get_all_edges():
        result.append({
            "from_id": edge.from_id,
            "to_id": edge.to_id,
            "distance": edge.distance,
            "capacity": edge.capacity,
            "condition": edge.condition,
            "traffic": edge.traffic,
            "is_existing": edge.is_existing,
            "construction_cost": edge.construction_cost,
        })
    return result


# ---------------------------------------------------------------------------
# Database endpoints
# ---------------------------------------------------------------------------
@app.get("/api/db/summary")
def db_summary():
    assert db is not None
    return db.network_summary()


@app.get("/api/db/demand-pairs")
def db_demand_pairs():
    assert db is not None
    return db.top_demand_pairs(limit=10)


@app.get("/api/db/bus-routes")
def db_bus_routes():
    assert db is not None
    return db.get_bus_routes()


@app.get("/api/db/all-contents")
def db_all_contents():
    """Return all database contents as JSON for the frontend."""
    assert db is not None
    nodes = [dict(n) for n in db.get_all_nodes()]
    existing_roads = [dict(r) for r in db.get_all_roads(existing_only=True)]
    candidate_roads = [dict(r) for r in db.get_candidate_roads()]
    bus_routes = db.get_bus_routes()
    demand = db.get_transport_demand()
    metro_lines = [dict(m) for m in db.con.execute("SELECT * FROM metro_lines").fetchall()]
    return {
        "nodes": nodes,
        "existing_roads": existing_roads,
        "candidate_roads": candidate_roads,
        "bus_routes": bus_routes,
        "demand": demand,
        "metro_lines": metro_lines,
    }


# ---------------------------------------------------------------------------
# Algorithm endpoints
# ---------------------------------------------------------------------------
@app.post("/api/algorithms/shortest-path")
def algo_shortest_path(req: ShortestPathRequest):
    assert graph is not None
    try:
        cost, path, report = dijkstra(graph, req.source, req.target, req.time_of_day)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid node ID: {exc}")

    if not path:
        raise HTTPException(status_code=404, detail="No route found")

    # Compute total distance and congestion level
    total_distance = sum(r["distance_km"] for r in report)
    avg_congestion_pct = sum(r["congestion_pct"] for r in report) / len(report) if report else 0

    if avg_congestion_pct < 70:
        congestion_level = "LOW"
    elif avg_congestion_pct < 90:
        congestion_level = "MEDIUM"
    else:
        congestion_level = "HIGH"

    # Estimate time: distance / avg speed (modified by congestion)
    avg_speed = 40 * (1 - avg_congestion_pct / 200)  # km/h rough estimate
    estimated_time = round((total_distance / max(avg_speed, 5)) * 60, 1)  # minutes

    # Reliability: inverse of congestion
    reliability = round(max(0, 100 - avg_congestion_pct), 1)

    # Build path names
    path_names = [graph.get_node(nid).name for nid in path]
    best_path = " -> ".join(path_names)
    
    # Format path steps for frontend
    path_steps = []
    for r in report:
        path_steps.append({
            "step": r["edge"],
            "distance_km": r["distance_km"],
            "flow": r["flow"],
            "capacity": r["capacity"],
            "congestion": f"{r['congestion_pct']:.1f}%"
        })
    
    # Calculate complexity notation
    num_nodes = len(graph.nodes)
    num_edges = len(graph.get_all_edges(existing_only=True))
    complexity = f"[Complexity] O((V + E) log V) where V={num_nodes}, E={num_edges}"

    return {
        "path": path,
        "path_names": path_names,
        "best_path": best_path,
        "total_distance": round(total_distance, 2),
        "total_cost": round(cost, 2),
        "total_congestion_cost": round(cost, 2),
        "congestion_level": congestion_level,
        "avg_congestion_pct": round(avg_congestion_pct, 1),
        "estimated_time": estimated_time,
        "reliability": reliability,
        "report": report,
        "path_steps": path_steps,
        "complexity": complexity,
    }


@app.post("/api/algorithms/emergency-routing")
def algo_emergency(req: EmergencyRequest):
    assert graph is not None
    try:
        path, estimated_time, explored = astar_emergency(graph, req.incident_node)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid node ID: {exc}")

    if not path:
        raise HTTPException(status_code=404, detail="No emergency path found")

    destination = path[-1]
    dest_node = graph.get_node(destination)
    path_names = [graph.get_node(nid).name for nid in path]
    total_distance = sum(
        graph.get_edge(a, b).distance
        for a, b in zip(path, path[1:])
        if graph.get_edge(a, b)
    )

    return {
        "path": path,
        "path_names": path_names,
        "nearest_facility": dest_node.name,
        "facility_type": dest_node.node_type,
        "distance": round(total_distance, 2),
        "estimated_time": round(estimated_time, 2),
        "nodes_explored": explored,
    }


@app.post("/api/algorithms/mst")
def algo_mst():
    assert graph is not None
    result = modified_kruskal_mst(graph)

    edges_data = []
    for edge in result.edges:
        edges_data.append({
            "from_id": edge.from_id,
            "to_id": edge.to_id,
            "distance": edge.distance,
            "condition": edge.condition,
        })

    mandatory_data = []
    for edge in result.mandatory_edges:
        mandatory_data.append({
            "from_id": edge.from_id,
            "to_id": edge.to_id,
            "distance": edge.distance,
        })

    return {
        "edges": edges_data,
        "mandatory_edges": mandatory_data,
        "total_cost": round(result.total_cost_estimate, 2),
        "total_distance": round(result.total_distance, 2),
        "suggested_roads": result.suggested_new_roads,
    }


@app.post("/api/algorithms/bus-allocation")
def algo_bus_allocation(req: BusAllocationRequest):
    assert db is not None
    routes = db.get_bus_routes()
    selected, max_passengers, _ = optimize_bus_allocation(routes, req.budget)

    return {
        "selected_routes": selected,
        "total_buses": sum(r["buses_assigned"] for r in selected),
        "max_passengers": max_passengers,
        "coverage": round(len(selected) / len(routes) * 100, 1) if routes else 0,
    }


@app.post("/api/algorithms/road-maintenance")
def algo_road_maintenance(req: RoadMaintenanceRequest):
    assert graph is not None
    roads = graph.get_all_edges(existing_only=True)
    selected, total_improvement = road_maintenance_allocation(roads, req.budget)

    return {
        "selected_roads": selected,
        "total_cost": sum(item["cost"] for item in selected),
        "roads_fixed": len(selected),
        "total_improvement": total_improvement,
    }


@app.post("/api/algorithms/traffic-signals")
def algo_traffic_signals(req: TrafficSignalsRequest):
    assert graph is not None
    try:
        result = optimize_traffic_signals(graph, req.node_id, req.time_of_day)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid node ID: {exc}")

    signal_plan = result["signal_plan"]
    critical = result["critical_roads"]

    # Compute an optimization score
    total_green = sum(signal_plan.values())
    max_possible = len(signal_plan) * 120
    optimization_score = round((total_green / max_possible * 100) if max_possible > 0 else 0, 1)

    return {
        "green_times": signal_plan,
        "overloaded_roads": critical,
        "optimization_score": optimization_score,
    }


@app.post("/api/algorithms/memoized-planner")
def algo_memoized_planner(req: MemoizedPlannerRequest):
    assert graph is not None
    try:
        result = memoized_route_planner(graph, req.source, req.destinations, req.time_of_day)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid node ID: {exc}")

    routes = []
    total_distance = 0.0
    for target, data in result["results"].items():
        path_names = [graph.get_node(nid).name for nid in data["path"]] if data["path"] else []
        routes.append({
            "target": target,
            "target_name": graph.get_node(target).name if target in graph.nodes else target,
            "cost": round(data["cost"], 2),
            "path": data["path"],
            "path_names": path_names,
        })
        total_distance += data["cost"]

    unique_targets = len(set(req.destinations))
    cache_hits = len(req.destinations) - unique_targets

    return {
        "routes": routes,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(result["cache_hit_rate"], 2),
        "total_distance": round(total_distance, 2),
    }


@app.post("/api/algorithms/airport-access")
def algo_airport_access(req: AirportAccessRequest):
    """Find fastest route to Cairo International Airport from any node."""
    assert graph is not None
    try:
        result = route_to_airport(graph, req.source, req.time_of_day)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid node ID: {exc}")

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    return result


# ---------------------------------------------------------------------------
# Simulation endpoints
# ---------------------------------------------------------------------------
@app.post("/api/simulation/rush-hour")
def sim_rush_hour(req: RushHourRequest):
    assert graph is not None and db is not None
    try:
        result = Scenario.run_rush_hour(graph, req.time_of_day, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    congested = result.get("congested_roads", [])
    avg_cong = round(
        sum(pct for _, pct in congested) / len(congested), 1
    ) if congested else 0

    recommendations = result.get("alternate_routes", [])

    return {
        "congested_roads": [{"road": road, "congestion_pct": pct} for road, pct in congested],
        "avg_congestion": avg_cong,
        "recommendations": recommendations,
        "top_pairs": result.get("top_pairs", []),
    }


@app.post("/api/simulation/road-closure")
def sim_road_closure(req: RoadClosureRequest):
    assert graph is not None and db is not None
    
    # Check if the road exists
    edge = graph.get_edge(req.from_node, req.to_node)
    if edge is None or not edge.is_existing:
        from_node = graph.get_node(req.from_node)
        to_node = graph.get_node(req.to_node)
        from_name = from_node.name if from_node else req.from_node
        to_name = to_node.name if to_node else req.to_node
        raise HTTPException(
            status_code=400, 
            detail=f"No direct road exists between {from_name} and {to_name}. Please select two nodes that have a direct road connection."
        )
    
    try:
        result = Scenario.run_road_closure(graph, req.from_node, req.to_node, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    impacted = result.get("impacted_routes", [])
    impact_score = len(impacted)

    return {
        "affected_routes": [
            {"from": r[0], "to": r[1], "extra_cost": r[2], "impact": r[3]}
            for r in impacted
        ],
        "impact_score": impact_score,
    }


@app.post("/api/simulation/new-road-analysis")
def sim_new_road():
    assert graph is not None and db is not None
    try:
        result = Scenario.run_new_road_analysis(graph, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    projected = result.get("projected_reduction", [])
    return {
        "best_candidates": [
            {"road": r[0], "cost_effectiveness": r[1], "congestion_reduction": r[2]}
            for r in projected
        ],
    }


# ---------------------------------------------------------------------------
# Machine-learning endpoints
# ---------------------------------------------------------------------------
@app.get("/api/ml/congestion-model")
def ml_congestion_model():
    """Train the congestion model and return evaluation details for the UI."""
    artifacts = train_congestion_model()
    if artifacts is None:
        raise HTTPException(
            status_code=503,
            detail="scikit-learn is not installed. Install it with: pip install scikit-learn",
        )

    example_time = "morning"
    example_flow = 1800.0
    example_capacity = 1500.0
    example_distance = 6.5
    predicted = predict_congestion(
        artifacts.model,
        time_of_day=example_time,
        flow=example_flow,
        capacity=example_capacity,
        distance=example_distance,
    )
    static_congestion = example_flow / example_capacity
    old_weight = example_distance * (1 + static_congestion)
    ml_weight = example_distance * (1 + predicted)

    sample_predictions = [
        {
            "index": index,
            "actual": round(actual, 4),
            "predicted": round(predicted_value, 4),
            "absolute_error": round(abs(actual - predicted_value), 4),
        }
        for index, (actual, predicted_value) in enumerate(artifacts.sample_predictions, start=1)
    ]
    avg_abs_error = (
        sum(item["absolute_error"] for item in sample_predictions) / len(sample_predictions)
        if sample_predictions
        else 0.0
    )

    return {
        "model_name": "Linear Regression",
        "dataset_origin": artifacts.dataset_origin,
        "sample_count": artifacts.sample_count,
        "mse": round(artifacts.mse, 6),
        "average_absolute_error": round(avg_abs_error, 6),
        "features": ["time_of_day", "flow", "capacity", "distance"],
        "sample_predictions": sample_predictions,
        "weight_comparison": {
            "time_of_day": example_time,
            "flow": example_flow,
            "capacity": example_capacity,
            "distance": example_distance,
            "static_congestion": round(static_congestion, 4),
            "predicted_congestion": round(predicted, 4),
            "old_weight": round(old_weight, 4),
            "ml_weight": round(ml_weight, 4),
        },
    }


@app.post("/api/ml/predict-congestion")
def ml_predict_congestion(req: CongestionPredictionRequest):
    """Predict congestion for user-provided road conditions."""
    artifacts = train_congestion_model()
    if artifacts is None:
        raise HTTPException(
            status_code=503,
            detail="scikit-learn is not installed. Install it with: pip install scikit-learn",
        )
    if req.capacity <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be greater than zero")
    if req.flow < 0 or req.distance <= 0:
        raise HTTPException(status_code=400, detail="Flow must be non-negative and distance must be greater than zero")

    static_congestion = req.flow / req.capacity
    predicted = predict_congestion(
        artifacts.model,
        time_of_day=req.time_of_day,
        flow=req.flow,
        capacity=req.capacity,
        distance=req.distance,
    )
    old_weight = req.distance * (1 + static_congestion)
    ml_weight = req.distance * (1 + predicted)

    return {
        "time_of_day": req.time_of_day,
        "flow": req.flow,
        "capacity": req.capacity,
        "distance": req.distance,
        "static_congestion": round(static_congestion, 4),
        "predicted_congestion": round(predicted, 4),
        "old_weight": round(old_weight, 4),
        "ml_weight": round(ml_weight, 4),
        "model_name": "Linear Regression",
        "dataset_origin": artifacts.dataset_origin,
    }


# ---------------------------------------------------------------------------
# Visualization endpoints
# ---------------------------------------------------------------------------
@app.post("/api/visualization/race")
def visualization_race(req: AlgorithmRaceRequest):
    """Return side-by-side algorithm traces for the race visualizer.

    This endpoint calls visualization-only runners and does not modify the
    existing production algorithm implementations.
    """
    assert graph is not None
    if req.source not in graph.nodes or req.target not in graph.nodes:
        raise HTTPException(status_code=400, detail="Invalid source or target node")

    supported = {"dijkstra", "astar", "greedy", "bfs"}
    if req.algorithm_a not in supported or req.algorithm_b not in supported:
        raise HTTPException(status_code=400, detail="Supported algorithms: dijkstra, astar, greedy, bfs")

    left = run_visual_trace(graph, req.algorithm_a, req.source, req.target, req.time_of_day)
    right = run_visual_trace(graph, req.algorithm_b, req.source, req.target, req.time_of_day)

    if left["visited_count"] < right["visited_count"]:
        winner = left["label"]
        reason = "visited fewer nodes"
        explanation = f"{left['label']} explored fewer nodes before reaching the target."
    elif right["visited_count"] < left["visited_count"]:
        winner = right["label"]
        reason = "visited fewer nodes"
        explanation = f"{right['label']} explored fewer nodes before reaching the target."
    elif left["execution_time_ms"] <= right["execution_time_ms"]:
        winner = left["label"]
        reason = "completed in less measured time"
        explanation = f"{left['label']} had the lower measured runtime for this trace."
    else:
        winner = right["label"]
        reason = "completed in less measured time"
        explanation = f"{right['label']} had the lower measured runtime for this trace."

    if left["path_length"] != right["path_length"]:
        shorter = left if left["path_length"] < right["path_length"] else right
        explanation += f" {shorter['label']} also produced the shorter physical route."

    return {
        "source": req.source,
        "target": req.target,
        "source_name": graph.get_node(req.source).name,
        "target_name": graph.get_node(req.target).name,
        "time_of_day": req.time_of_day,
        "left": left,
        "right": right,
        "summary": {
            "winner": winner,
            "reason": reason,
            "explanation": explanation,
            "step_count": max(len(left["steps"]), len(right["steps"])),
        },
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
