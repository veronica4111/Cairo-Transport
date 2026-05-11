"""Embedded dataset and graph builder for the Cairo transportation project."""

from __future__ import annotations

from typing import Any

from cairo_transport.graph import TransportGraph

TIME_SLOTS = ("morning", "afternoon", "evening", "night")
MEDICAL_FACILITY_IDS = ("F9", "F10")
MANDATORY_MST_NODE_IDS = ("F9", "F10", "13")

DISTRICTS: list[dict[str, Any]] = [
    {"id": "1", "name": "Maadi", "population": 250000, "type": "Residential", "x": 31.25, "y": 29.96},
    {"id": "2", "name": "Nasr City", "population": 500000, "type": "Mixed", "x": 31.34, "y": 30.06},
    {"id": "3", "name": "Downtown Cairo", "population": 100000, "type": "Business", "x": 31.24, "y": 30.04},
    {"id": "4", "name": "New Cairo", "population": 300000, "type": "Residential", "x": 31.47, "y": 30.03},
    {"id": "5", "name": "Heliopolis", "population": 200000, "type": "Mixed", "x": 31.32, "y": 30.09},
    {"id": "6", "name": "Zamalek", "population": 50000, "type": "Residential", "x": 31.22, "y": 30.06},
    {"id": "7", "name": "6th October City", "population": 400000, "type": "Mixed", "x": 30.98, "y": 29.93},
    {"id": "8", "name": "Giza", "population": 500000, "type": "Mixed", "x": 31.21, "y": 29.99},
    {"id": "9", "name": "Mohandessin", "population": 180000, "type": "Business", "x": 31.20, "y": 30.05},
    {"id": "10", "name": "Dokki", "population": 220000, "type": "Mixed", "x": 31.21, "y": 30.03},
    {"id": "11", "name": "Shubra", "population": 450000, "type": "Residential", "x": 31.24, "y": 30.11},
    {"id": "12", "name": "Helwan", "population": 350000, "type": "Industrial", "x": 31.33, "y": 29.85},
    {"id": "13", "name": "New Administrative Capital", "population": 50000, "type": "Government", "x": 31.80, "y": 30.02},
    {"id": "14", "name": "Al Rehab", "population": 120000, "type": "Residential", "x": 31.49, "y": 30.06},
    {"id": "15", "name": "Sheikh Zayed", "population": 150000, "type": "Residential", "x": 30.94, "y": 30.01},
]

FACILITIES: list[dict[str, Any]] = [
    {"id": "F1", "name": "Cairo International Airport", "type": "Airport", "x": 31.41, "y": 30.11},
    {"id": "F2", "name": "Ramses Railway Station", "type": "Transport Hub", "x": 31.25, "y": 30.06},
    {"id": "F3", "name": "Cairo University", "type": "Education", "x": 31.21, "y": 30.03},
    {"id": "F4", "name": "Al-Azhar University", "type": "Education", "x": 31.26, "y": 30.05},
    {"id": "F5", "name": "Egyptian Museum", "type": "Tourism", "x": 31.23, "y": 30.05},
    {"id": "F6", "name": "Cairo International Stadium", "type": "Sports", "x": 31.30, "y": 30.07},
    {"id": "F7", "name": "Smart Village", "type": "Business", "x": 30.97, "y": 30.07},
    {"id": "F8", "name": "Cairo Festival City", "type": "Commercial", "x": 31.40, "y": 30.03},
    {"id": "F9", "name": "Qasr El Aini Hospital", "type": "Medical", "x": 31.23, "y": 30.03},
    {"id": "F10", "name": "Maadi Military Hospital", "type": "Medical", "x": 31.25, "y": 29.95},
]

EXISTING_ROADS: list[dict[str, Any]] = [
    {"from": "1", "to": "3", "distance_km": 8.5, "capacity": 3000, "condition": 7},
    {"from": "1", "to": "8", "distance_km": 6.2, "capacity": 2500, "condition": 6},
    {"from": "2", "to": "3", "distance_km": 5.9, "capacity": 2800, "condition": 8},
    {"from": "2", "to": "5", "distance_km": 4.0, "capacity": 3200, "condition": 9},
    {"from": "3", "to": "5", "distance_km": 6.1, "capacity": 3500, "condition": 7},
    {"from": "3", "to": "6", "distance_km": 3.2, "capacity": 2000, "condition": 8},
    {"from": "3", "to": "9", "distance_km": 4.5, "capacity": 2600, "condition": 6},
    {"from": "3", "to": "10", "distance_km": 3.8, "capacity": 2400, "condition": 7},
    {"from": "4", "to": "2", "distance_km": 15.2, "capacity": 3800, "condition": 9},
    {"from": "4", "to": "14", "distance_km": 5.3, "capacity": 3000, "condition": 10},
    {"from": "5", "to": "11", "distance_km": 7.9, "capacity": 3100, "condition": 7},
    {"from": "6", "to": "9", "distance_km": 2.2, "capacity": 1800, "condition": 8},
    {"from": "7", "to": "8", "distance_km": 24.5, "capacity": 3500, "condition": 8},
    {"from": "7", "to": "15", "distance_km": 9.8, "capacity": 3000, "condition": 9},
    {"from": "8", "to": "10", "distance_km": 3.3, "capacity": 2200, "condition": 7},
    {"from": "8", "to": "12", "distance_km": 14.8, "capacity": 2600, "condition": 5},
    {"from": "9", "to": "10", "distance_km": 2.1, "capacity": 1900, "condition": 7},
    {"from": "10", "to": "11", "distance_km": 8.7, "capacity": 2400, "condition": 6},
    {"from": "11", "to": "F2", "distance_km": 3.6, "capacity": 2200, "condition": 7},
    {"from": "12", "to": "1", "distance_km": 12.7, "capacity": 2800, "condition": 6},
    {"from": "13", "to": "4", "distance_km": 45.0, "capacity": 4000, "condition": 10},
    {"from": "14", "to": "13", "distance_km": 35.5, "capacity": 3800, "condition": 9},
    {"from": "15", "to": "7", "distance_km": 9.8, "capacity": 3000, "condition": 9},
    {"from": "F1", "to": "5", "distance_km": 7.5, "capacity": 3500, "condition": 9},
    {"from": "F1", "to": "2", "distance_km": 9.2, "capacity": 3200, "condition": 8},
    {"from": "F2", "to": "3", "distance_km": 2.5, "capacity": 2000, "condition": 7},
    {"from": "F7", "to": "15", "distance_km": 8.3, "capacity": 2800, "condition": 8},
    {"from": "F8", "to": "4", "distance_km": 6.1, "capacity": 3000, "condition": 9},
    # Medical facilities connections
    {"from": "F9", "to": "3", "distance_km": 1.2, "capacity": 1500, "condition": 8},
    {"from": "F9", "to": "10", "distance_km": 1.0, "capacity": 1500, "condition": 8},
    {"from": "F10", "to": "1", "distance_km": 1.5, "capacity": 1500, "condition": 7},
    {"from": "F10", "to": "12", "distance_km": 11.0, "capacity": 2000, "condition": 6},
]

CANDIDATE_ROADS: list[dict[str, Any]] = [
    {"from": "1", "to": "4", "distance_km": 22.8, "capacity": 4000, "construction_cost": 450},
    {"from": "1", "to": "14", "distance_km": 25.3, "capacity": 3800, "construction_cost": 500},
    {"from": "2", "to": "13", "distance_km": 48.2, "capacity": 4500, "construction_cost": 950},
    {"from": "3", "to": "13", "distance_km": 56.7, "capacity": 4500, "construction_cost": 1100},
    {"from": "5", "to": "4", "distance_km": 16.8, "capacity": 3500, "construction_cost": 320},
    {"from": "6", "to": "8", "distance_km": 7.5, "capacity": 2500, "construction_cost": 150},
    {"from": "7", "to": "13", "distance_km": 82.3, "capacity": 4000, "construction_cost": 1600},
    {"from": "9", "to": "11", "distance_km": 6.9, "capacity": 2800, "construction_cost": 140},
    {"from": "10", "to": "F7", "distance_km": 27.4, "capacity": 3200, "construction_cost": 550},
    {"from": "11", "to": "13", "distance_km": 62.1, "capacity": 4200, "construction_cost": 1250},
    {"from": "12", "to": "14", "distance_km": 30.5, "capacity": 3600, "construction_cost": 610},
    {"from": "14", "to": "5", "distance_km": 18.2, "capacity": 3300, "construction_cost": 360},
    {"from": "15", "to": "9", "distance_km": 22.7, "capacity": 3000, "construction_cost": 450},
    {"from": "F1", "to": "13", "distance_km": 40.2, "capacity": 4000, "construction_cost": 800},
    {"from": "F7", "to": "9", "distance_km": 26.8, "capacity": 3200, "construction_cost": 540},
]

TRAFFIC_FLOWS: list[dict[str, Any]] = [
    {"road_id": "1-3", "morning": 2800, "afternoon": 1500, "evening": 2600, "night": 800},
    {"road_id": "1-8", "morning": 2200, "afternoon": 1200, "evening": 2100, "night": 600},
    {"road_id": "2-3", "morning": 2700, "afternoon": 1400, "evening": 2500, "night": 700},
    {"road_id": "2-5", "morning": 3000, "afternoon": 1600, "evening": 2800, "night": 650},
    {"road_id": "3-5", "morning": 3200, "afternoon": 1700, "evening": 3100, "night": 800},
    {"road_id": "3-6", "morning": 1800, "afternoon": 1400, "evening": 1900, "night": 500},
    {"road_id": "3-9", "morning": 2400, "afternoon": 1300, "evening": 2200, "night": 550},
    {"road_id": "3-10", "morning": 2300, "afternoon": 1200, "evening": 2100, "night": 500},
    {"road_id": "4-2", "morning": 3600, "afternoon": 1800, "evening": 3300, "night": 750},
    {"road_id": "4-14", "morning": 2800, "afternoon": 1600, "evening": 2600, "night": 600},
    {"road_id": "5-11", "morning": 2900, "afternoon": 1500, "evening": 2700, "night": 650},
    {"road_id": "6-9", "morning": 1700, "afternoon": 1300, "evening": 1800, "night": 450},
    {"road_id": "7-8", "morning": 3200, "afternoon": 1700, "evening": 3000, "night": 700},
    {"road_id": "7-15", "morning": 2800, "afternoon": 1500, "evening": 2600, "night": 600},
    {"road_id": "8-10", "morning": 2000, "afternoon": 1100, "evening": 1900, "night": 450},
    {"road_id": "8-12", "morning": 2400, "afternoon": 1300, "evening": 2200, "night": 500},
    {"road_id": "9-10", "morning": 1800, "afternoon": 1200, "evening": 1700, "night": 400},
    {"road_id": "10-11", "morning": 2200, "afternoon": 1300, "evening": 2100, "night": 500},
    {"road_id": "11-F2", "morning": 2100, "afternoon": 1200, "evening": 2000, "night": 450},
    {"road_id": "12-1", "morning": 2600, "afternoon": 1400, "evening": 2400, "night": 550},
    {"road_id": "13-4", "morning": 3800, "afternoon": 2000, "evening": 3500, "night": 800},
    {"road_id": "14-13", "morning": 3600, "afternoon": 1900, "evening": 3300, "night": 750},
    {"road_id": "15-7", "morning": 2800, "afternoon": 1500, "evening": 2600, "night": 600},
    {"road_id": "F1-5", "morning": 3300, "afternoon": 2200, "evening": 3100, "night": 1200},
    {"road_id": "F1-2", "morning": 3000, "afternoon": 2000, "evening": 2800, "night": 1100},
    {"road_id": "F2-3", "morning": 1900, "afternoon": 1600, "evening": 1800, "night": 900},
    {"road_id": "F7-15", "morning": 2600, "afternoon": 1500, "evening": 2400, "night": 550},
    {"road_id": "F8-4", "morning": 2800, "afternoon": 1600, "evening": 2600, "night": 600},
    # Medical facilities traffic
    {"road_id": "F9-3", "morning": 1200, "afternoon": 800, "evening": 1100, "night": 400},
    {"road_id": "F9-10", "morning": 1000, "afternoon": 700, "evening": 900, "night": 350},
    {"road_id": "F10-1", "morning": 1100, "afternoon": 750, "evening": 1000, "night": 380},
    {"road_id": "F10-12", "morning": 1500, "afternoon": 900, "evening": 1400, "night": 450},
]

METRO_LINES: list[dict[str, Any]] = [
    {"id": "M1", "name": "Line 1 (Helwan-New Marg)", "stations": ["12", "1", "3", "F2", "11"], "daily_passengers": 1500000},
    {"id": "M2", "name": "Line 2 (Shubra-Giza)", "stations": ["11", "F2", "3", "10", "8"], "daily_passengers": 1200000},
    {"id": "M3", "name": "Line 3 (Airport-Imbaba)", "stations": ["F1", "5", "2", "3", "9"], "daily_passengers": 800000},
]

BUS_ROUTES: list[dict[str, Any]] = [
    {"id": "B1", "stops": ["1", "3", "6", "9", "2", "5"], "buses_assigned": 35, "daily_passengers": 50000},
    {"id": "B2", "stops": ["7", "15", "8", "10", "3"], "buses_assigned": 30, "daily_passengers": 42000},
    {"id": "B3", "stops": ["2", "5", "F1"], "buses_assigned": 20, "daily_passengers": 28000},
    {"id": "B4", "stops": ["4", "14", "2", "3"], "buses_assigned": 22, "daily_passengers": 31000},
    {"id": "B5", "stops": ["8", "12", "1"], "buses_assigned": 18, "daily_passengers": 25000},
    {"id": "B6", "stops": ["11", "5", "2"], "buses_assigned": 24, "daily_passengers": 33000},
    {"id": "B7", "stops": ["13", "4", "14"], "buses_assigned": 15, "daily_passengers": 21000},
    {"id": "B8", "stops": ["F7", "15", "7"], "buses_assigned": 12, "daily_passengers": 17000},
    {"id": "B9", "stops": ["1", "8", "10", "9", "6"], "buses_assigned": 28, "daily_passengers": 39000},
    {"id": "B10", "stops": ["F8", "4", "2", "5"], "buses_assigned": 20, "daily_passengers": 28000},
]

PUBLIC_TRANSPORT_DEMAND: list[dict[str, Any]] = [
    {"from": "3", "to": "5", "daily_passengers": 15000},
    {"from": "1", "to": "3", "daily_passengers": 12000},
    {"from": "2", "to": "3", "daily_passengers": 18000},
    {"from": "F2", "to": "11", "daily_passengers": 25000},
    {"from": "F1", "to": "3", "daily_passengers": 20000},
    {"from": "7", "to": "3", "daily_passengers": 14000},
    {"from": "4", "to": "3", "daily_passengers": 16000},
    {"from": "8", "to": "3", "daily_passengers": 22000},
    {"from": "3", "to": "9", "daily_passengers": 13000},
    {"from": "5", "to": "2", "daily_passengers": 17000},
    {"from": "11", "to": "3", "daily_passengers": 24000},
    {"from": "12", "to": "3", "daily_passengers": 11000},
    {"from": "1", "to": "8", "daily_passengers": 9000},
    {"from": "7", "to": "F7", "daily_passengers": 18000},
    {"from": "4", "to": "F8", "daily_passengers": 12000},
    {"from": "13", "to": "3", "daily_passengers": 8000},
    {"from": "14", "to": "4", "daily_passengers": 7000},
]


def traffic_lookup() -> dict[str, dict[str, int]]:
    """Return a bidirectional mapping from road ID to time-dependent flow."""
    lookup: dict[str, dict[str, int]] = {}
    for row in TRAFFIC_FLOWS:
        a, b = row["road_id"].split("-")
        payload = {slot: int(row[slot]) for slot in TIME_SLOTS}
        lookup[f"{a}-{b}"] = payload
        lookup[f"{b}-{a}"] = payload
    return lookup


def build_graph() -> TransportGraph:
    """Create the transport graph with nodes, roads, and candidate links."""
    graph = TransportGraph()

    for district in DISTRICTS:
        graph.add_node(district["id"], district["name"], int(district["population"]), district["type"], float(district["x"]), float(district["y"]))

    for facility in FACILITIES:
        graph.add_node(facility["id"], facility["name"], 0, facility["type"], float(facility["x"]), float(facility["y"]))

    traffic = traffic_lookup()

    for road in EXISTING_ROADS:
        graph.add_edge(
            from_id=road["from"],
            to_id=road["to"],
            distance=float(road["distance_km"]),
            capacity=int(road["capacity"]),
            condition=int(road["condition"]),
            traffic=traffic.get(f"{road['from']}-{road['to']}", {slot: 0 for slot in TIME_SLOTS}),
            is_existing=True,
            construction_cost=None,
        )

    for road in CANDIDATE_ROADS:
        graph.add_edge(
            from_id=road["from"],
            to_id=road["to"],
            distance=float(road["distance_km"]),
            capacity=int(road["capacity"]),
            condition=8,
            traffic={slot: 0 for slot in TIME_SLOTS},
            is_existing=False,
            construction_cost=float(road["construction_cost"]),
        )

    return graph
