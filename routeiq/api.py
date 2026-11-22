from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from routeiq.engine import NODES, plan_fleet, shortest_path

app = FastAPI(
    title="RouteIQ API",
    version="1.0.0",
    description="Demo route planning and capacity-aware fleet dispatch API.",
)


class RouteRequest(BaseModel):
    start: str
    destination: str

    @field_validator("start", "destination")
    @classmethod
    def validate_node(cls, value: str) -> str:
        if value not in NODES:
            raise ValueError("Location is not in the RouteIQ demo road network")
        return value


class OrderInput(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    destination: str
    load: int = Field(default=1, ge=1, le=100)
    priority: int = Field(default=1, ge=1, le=5)
    deadline: str = "23:59"

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, value: str) -> str:
        if value not in NODES or value == "depot":
            raise ValueError("Destination must be a delivery node in the demo network")
        return value


class VehicleInput(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    driver: str = Field(min_length=1, max_length=80)
    capacity: int = Field(ge=1, le=100)


class FleetPlanRequest(BaseModel):
    orders: list[OrderInput]
    vehicles: list[VehicleInput]
    traffic_factor: float = Field(default=1.0, ge=1.0, le=3.0)
    average_speed_kmh: float = Field(default=28.0, gt=0, le=120)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "routeiq-api"}


@app.get("/api/v1/locations")
async def locations() -> dict[str, Any]:
    return {"locations": NODES}


@app.post("/api/v1/route")
async def route(request: RouteRequest) -> dict[str, Any]:
    try:
        result = shortest_path(request.start, request.destination)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        **result,
        "start": request.start,
        "destination": request.destination,
        "data_source": "illustrative_demo_road_graph",
    }


@app.post("/api/v1/dispatch")
async def dispatch(request: FleetPlanRequest) -> dict[str, Any]:
    try:
        plans = plan_fleet(
            [order.model_dump() for order in request.orders],
            [vehicle.model_dump() for vehicle in request.vehicles],
            traffic_factor=request.traffic_factor,
            average_speed_kmh=request.average_speed_kmh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    assigned_ids = {order_id for plan in plans for order_id in plan["order_ids"]}
    requested_ids = {order.id for order in request.orders}
    unassigned = sorted(requested_ids - assigned_ids)
    return {
        "plans": plans,
        "unassigned_order_ids": unassigned,
        "data_source": "illustrative_demo_road_graph",
        "notice": "Distances and ETAs are estimates from demo road edges, not live navigation data.",
    }
