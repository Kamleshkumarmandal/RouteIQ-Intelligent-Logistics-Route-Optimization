# RouteIQ — Intelligent Logistics & Route Optimization

RouteIQ is a portfolio project that demonstrates graph algorithms, fleet dispatch, vehicle capacity planning and reliability-minded API design.

It includes a **Streamlit demo dashboard** and a separate **FastAPI route planning service**. The original road network is intentionally small and inspectable so routing and dispatch decisions can be explained clearly.

## Current demo features

- Chennai-inspired sample location network and road-edge table
- Dijkstra shortest-path route explorer
- Capacity-aware greedy order-to-vehicle assignment
- Dispatch plan with round-trip distance, stop order and estimated time
- Traffic multiplier and average-speed controls
- Interactive PyDeck route visualization
- Order creation and vehicle overview
- CSV export of dispatch assignments
- FastAPI endpoints for health, locations, shortest path and fleet dispatch
- Unit and API tests plus a Streamlit render smoke test
- Dockerfile for the FastAPI service

## Important: sample data vs. real navigation

The coordinates and road-edge distances are **illustrative demo data**. Dijkstra optimizes over this configured graph; it does not query live maps, street geometry, road restrictions, or current traffic. The traffic multiplier is a scenario control, not a traffic feed. ETAs are calculated from estimated graph distance divided by an assumed average speed.

Do not use this prototype for real dispatch decisions. A production implementation needs a licensed road-routing provider or validated road graph, geocoding, traffic data, vehicle and time-window constraints, persistence, authenticated users, route recalculation, operational monitoring and safety review.

## Technology

- Python 3.11+
- Streamlit, Pandas and PyDeck
- FastAPI, Pydantic and Uvicorn
- Dijkstra shortest-path algorithm with a binary heap
- Greedy capacity-aware dispatch heuristic
- Python unittest suite
- Docker

## Run the Streamlit demo locally

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud

1. Sign in at https://share.streamlit.io using GitHub.
2. Select **Create app** and choose the existing repository.
3. Repository: `Kamleshkumarmandal/RouteIQ-Intelligent-Logistics-Route-Optimization`.
4. Branch: `main`.
5. Main file path: `streamlit_app.py`.
6. Click **Deploy**.

Streamlit uses the root `requirements.txt` and theme configuration in `.streamlit/config.toml`.

## Run the FastAPI service

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn routeiq.api:app --reload
```

Endpoints:

- `GET /health`
- `GET /api/v1/locations`
- `POST /api/v1/route`
- `POST /api/v1/dispatch`
- Interactive API docs: `/docs`

Example shortest-route request:

```json
{
  "start": "depot",
  "destination": "tambaram"
}
```

Example dispatch request:

```json
{
  "orders": [
    {"id": "ORD-1", "destination": "adyar", "load": 2, "priority": 5, "deadline": "10:30"}
  ],
  "vehicles": [
    {"id": "VAN-1", "driver": "Demo Driver", "capacity": 5}
  ],
  "traffic_factor": 1.2,
  "average_speed_kmh": 28
}
```

## Algorithms and complexity

- **Dijkstra:** Finds the minimum total edge-weight path using a binary heap; O((V + E) log V) for this adjacency-list implementation.
- **Haversine:** Computes great-circle distance between two configured coordinate pairs. This is included as a geographic comparison helper, not used as the road-edge weight.
- **Greedy dispatch:** Orders deliveries by priority, deadline and ID; assigns each to the available vehicle with the smallest incremental path distance that has sufficient remaining capacity. This is a heuristic, not a globally optimal vehicle-routing solver.
- **Traffic scenario:** Applies a configurable multiplier to the estimated total trip distance before converting it to estimated minutes.

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Project layout

```text
routeiq/
  __init__.py
  engine.py
  api.py
streamlit_app.py
tests/
  test_engine.py
  test_api.py
  test_streamlit_smoke.py
requirements.txt
Dockerfile
```

## Roadmap

- [ ] Replace demo graph with a maintained road graph or routing-provider API
- [ ] Add vehicle time windows, service times, driver shifts and vehicle types
- [ ] Add multi-depot and pickup/drop-off constraints
- [ ] Add a vehicle-routing optimization solver and compare it to the greedy baseline
- [ ] Persist orders, vehicles and trip history in PostgreSQL
- [ ] Add authenticated workspaces and role-based access
- [ ] Add background dispatch jobs and route updates
- [ ] Add live traffic/ETA provider integration and operational alerts
- [ ] Add integration, load and security tests

## License

MIT.
