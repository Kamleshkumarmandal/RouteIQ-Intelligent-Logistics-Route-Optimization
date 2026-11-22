"""RouteIQ route planning engine.

Distances are derived from an illustrative road graph. Coordinates and
edge costs are demo data, not live navigation or traffic-provider results.
"""
from __future__ import annotations

import heapq
import math
from typing import Any


NODES: dict[str, dict[str, Any]] = {
    "depot": {"name": "Central Depot", "lat": 13.0827, "lon": 80.2707},
    "anna_nagar": {"name": "Anna Nagar", "lat": 13.0850, "lon": 80.2101},
    "tnagar": {"name": "T. Nagar", "lat": 13.0418, "lon": 80.2341},
    "adyar": {"name": "Adyar", "lat": 13.0012, "lon": 80.2565},
    "guindy": {"name": "Guindy", "lat": 13.0067, "lon": 80.2206},
    "velachery": {"name": "Velachery", "lat": 12.9750, "lon": 80.2212},
    "porur": {"name": "Porur", "lat": 13.0358, "lon": 80.1562},
    "tambaram": {"name": "Tambaram", "lat": 12.9249, "lon": 80.1000},
    "perungudi": {"name": "Perungudi", "lat": 12.9600, "lon": 80.2450},
}

# Each edge is a demo road segment with an estimated distance in kilometres.
# The undirected network is deliberately small enough to inspect in an interview.
ROAD_EDGES: list[tuple[str, str, float]] = [
    ("depot", "anna_nagar", 7.7),
    ("depot", "tnagar", 6.0),
    ("depot", "adyar", 9.1),
    ("anna_nagar", "porur", 9.4),
    ("tnagar", "guindy", 5.4),
    ("tnagar", "adyar", 6.6),
    ("guindy", "velachery", 7.2),
    ("guindy", "porur", 9.0),
    ("adyar", "perungudi", 4.7),
    ("perungudi", "velachery", 5.8),
    ("velachery", "tambaram", 13.2),
    ("porur", "tambaram", 16.5),
    ("adyar", "velachery", 8.5),
]


def build_graph(edges: list[tuple[str, str, float]] = ROAD_EDGES) -> dict[str, list[tuple[str, float]]]:
    """Build an undirected weighted adjacency list."""
    graph: dict[str, list[tuple[str, float]]] = {node: [] for node in NODES}
    for left, right, distance in edges:
        if left not in graph or right not in graph:
            raise ValueError(f"Unknown node in edge: {left} - {right}")
        if distance <= 0:
            raise ValueError("Road distances must be positive")
        graph[left].append((right, float(distance)))
        graph[right].append((left, float(distance)))
    return graph


GRAPH = build_graph()


def haversine_km(a: str, b: str) -> float:
    """Great-circle distance between two configured nodes."""
    if a not in NODES or b not in NODES:
        raise ValueError("Unknown location")
    lat1, lon1 = math.radians(NODES[a]["lat"]), math.radians(NODES[a]["lon"])
    lat2, lon2 = math.radians(NODES[b]["lat"]), math.radians(NODES[b]["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def shortest_path(start: str, goal: str, graph: dict[str, list[tuple[str, float]]] = GRAPH) -> dict[str, Any]:
    """Dijkstra shortest path; O((V + E) log V) with a binary heap."""
    if start not in graph or goal not in graph:
        raise ValueError("Start or destination is not in the road graph")
    distances = {node: math.inf for node in graph}
    previous: dict[str, str | None] = {node: None for node in graph}
    distances[start] = 0.0
    heap: list[tuple[float, str]] = [(0.0, start)]

    while heap:
        current_distance, current = heapq.heappop(heap)
        if current_distance > distances[current]:
            continue
        if current == goal:
            break
        for neighbour, weight in graph[current]:
            candidate = current_distance + weight
            if candidate < distances[neighbour]:
                distances[neighbour] = candidate
                previous[neighbour] = current
                heapq.heappush(heap, (candidate, neighbour))

    if math.isinf(distances[goal]):
        raise ValueError(f"No route from {start} to {goal}")

    path = [goal]
    current = goal
    while current != start:
        parent = previous[current]
        if parent is None:
            raise ValueError(f"No route from {start} to {goal}")
        path.append(parent)
        current = parent
    path.reverse()
    return {"path": path, "distance_km": round(distances[goal], 2)}


def plan_fleet(
    orders: list[dict[str, Any]],
    vehicles: list[dict[str, Any]],
    traffic_factor: float = 1.0,
    average_speed_kmh: float = 28.0,
    depot: str = "depot",
) -> list[dict[str, Any]]:
    """Greedy capacity-aware dispatch using shortest-path costs between stops.

    Orders are assigned in priority/deadline order. For each order, choose the
    available vehicle with the least incremental route distance that has enough
    remaining capacity. Drivers return to the depot after their last stop.
    """
    if traffic_factor < 1 or traffic_factor > 3:
        raise ValueError("traffic_factor must be between 1 and 3")
    if average_speed_kmh <= 0:
        raise ValueError("average_speed_kmh must be positive")
    if depot not in GRAPH:
        raise ValueError("Unknown depot")

    vehicle_state = []
    seen_vehicle_ids: set[str] = set()
    for vehicle in vehicles:
        vid = str(vehicle["id"])
        if vid in seen_vehicle_ids:
            raise ValueError(f"Duplicate vehicle id: {vid}")
        seen_vehicle_ids.add(vid)
        capacity = int(vehicle["capacity"])
        if capacity <= 0:
            raise ValueError("Vehicle capacity must be positive")
        vehicle_state.append({
            "vehicle": vehicle,
            "remaining": capacity,
            "current": depot,
            "stops": [],
            "orders": [],
            "distance": 0.0,
        })

    seen_order_ids: set[str] = set()
    ordered = sorted(
        orders,
        key=lambda item: (-int(item.get("priority", 1)), str(item.get("deadline", "23:59")), str(item["id"])),
    )
    for order in ordered:
        oid = str(order["id"])
        destination = str(order["destination"])
        load = int(order.get("load", 1))
        if oid in seen_order_ids:
            raise ValueError(f"Duplicate order id: {oid}")
        seen_order_ids.add(oid)
        if destination not in GRAPH:
            raise ValueError(f"Unknown destination: {destination}")
        if load <= 0:
            raise ValueError("Order load must be positive")

        candidates = []
        for state in vehicle_state:
            if state["remaining"] < load:
                continue
            leg = shortest_path(state["current"], destination)["distance_km"]
            candidates.append((leg, str(state["vehicle"]["id"]), state))
        if not candidates:
            raise ValueError(f"No vehicle has enough remaining capacity for order {oid}")
        leg, _, chosen = min(candidates, key=lambda candidate: (candidate[0], candidate[1]))
        chosen["distance"] += leg
        chosen["remaining"] -= load
        chosen["current"] = destination
        chosen["stops"].append(destination)
        chosen["orders"].append(oid)

    plans = []
    for state in vehicle_state:
        if not state["orders"]:
            continue
        back = shortest_path(state["current"], depot)["distance_km"]
        total_distance = state["distance"] + back
        effective_distance = total_distance * traffic_factor
        eta_minutes = effective_distance / average_speed_kmh * 60
        route_nodes = [depot]
        current = depot
        for stop in state["stops"]:
            segment = shortest_path(current, stop)["path"]
            route_nodes.extend(segment[1:])
            current = stop
        segment = shortest_path(current, depot)["path"]
        route_nodes.extend(segment[1:])
        plans.append({
            "vehicle_id": str(state["vehicle"]["id"]),
            "driver": str(state["vehicle"]["driver"]),
            "capacity": int(state["vehicle"]["capacity"]),
            "used_capacity": int(state["vehicle"]["capacity"]) - int(state["remaining"]),
            "order_ids": list(state["orders"]),
            "stops": list(state["stops"]),
            "route_nodes": route_nodes,
            "distance_km": round(total_distance, 2),
            "estimated_minutes": round(eta_minutes, 1),
            "traffic_factor": traffic_factor,
        })
    return plans
