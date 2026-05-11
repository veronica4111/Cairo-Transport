# Cairo Smart City Transportation Network Optimization

An end-to-end transportation optimization project for Greater Cairo. The system models districts and public facilities as graph nodes, roads as weighted edges, and traffic demand as time-dependent congestion data. It exposes the same algorithmic core through a command-line demo, a FastAPI backend, and a React dashboard with interactive maps and visual traces.

## Highlights

- Database-backed graph model for Cairo districts, facilities, roads, demand pairs, bus routes, traffic flows, and candidate roads.
- Modified Kruskal minimum spanning tree for infrastructure planning with mandatory critical-node handling.
- Dijkstra, time-aware Dijkstra, and memoized route planning for congestion-aware shortest paths.
- A* emergency routing with nearest-facility search and signal-preemption weight reduction.
- Dynamic programming for bus allocation and road maintenance planning.
- Greedy traffic signal optimization based on incoming flow-to-capacity ratios.
- Scenario simulations for rush hour, road closures, emergency response, and proposed new roads.
- Linear-regression congestion prediction using scikit-learn when available.
- FastAPI API, React + TypeScript + Vite frontend, Leaflet maps, and NetworkX/Matplotlib generated visualizations.
- Docker Compose setup for running the backend and frontend together.

## Tech Stack

- **Backend:** Python, FastAPI, SQLite, NetworkX, Matplotlib, scikit-learn
- **Frontend:** React, TypeScript, Vite, Leaflet, Recharts, Framer Motion
- **Testing:** pytest
- **Deployment:** Docker Compose, Nginx frontend container

## Project Structure

```text
Algo project with DB/
|-- README.md
|-- api.py
|-- main.py
|-- congestion_ml_script.py
|-- docker-compose.yml
|-- Dockerfile.backend
|-- requirements.txt
|-- requirements-backend.txt
|-- cairo_transport/
|   |-- data.py
|   |-- database.py
|   |-- graph.py
|   |-- main.py
|   |-- ml_congestion.py
|   |-- simulation.py
|   |-- visual_runners.py
|   |-- visualization.py
|   `-- algorithms/
|       |-- astar.py
|       |-- dp_transit.py
|       |-- greedy_signals.py
|       |-- mst.py
|       `-- shortest_path.py
|-- docs/
|   `-- technical_report.md
|-- frontend/
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- package.json
|   |-- vite.config.ts
|   |-- index.html
|   `-- src/
|       |-- App.tsx
|       |-- api.ts
|       |-- main.tsx
|       |-- types.ts
|       |-- index.css
|       `-- components/
|-- output/
`-- tests/
    |-- test_algorithms.py
    |-- test_data_validation.py
    |-- test_database.py
    |-- test_graph.py
    `-- test_scenarios.py
```

Generated folders such as `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `.pytest_cache/`, and local virtual environments are not part of the source layout.

## Requirements

- Python 3.10 or newer
- Node.js and npm
- Docker Desktop, only if using the Docker workflow

## Quick Start

### 1. Install Python Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
python api.py
```

The API runs at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

### 3. Start the Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The dashboard usually runs at:

```text
http://localhost:5173
```

During development, `frontend/vite.config.ts` proxies `/api` requests to `http://localhost:8000`.

## CLI Demo

Run the interactive command-line demo from the project root:

```bash
python main.py
```

Useful demo flow:

1. Show the network summary.
2. Run shortest path from `7` to `3`.
3. Run emergency routing from `1`.
4. Run the modified MST and display the overlay.
5. Run bus allocation with budget `80`.
6. Run road maintenance with budget `350`.
7. Optimize signals at node `3`.
8. Run rush-hour and road-closure scenarios.
9. Test airport access routing from any node.

## Docker Workflow

Docker Compose runs the project as two services:

- `backend`: FastAPI on port `8000`
- `frontend`: Nginx serving the React production build on port `8080`

Build and start both services:

```bash
docker compose up --build
```

Open the app:

```text
http://localhost:8080
```

Open the backend docs:

```text
http://localhost:8000/docs
```

Run in the background:

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop the services:

```bash
docker compose down
```

Reset persisted Docker data:

```bash
docker compose down -v
```

The Docker backend uses `requirements-backend.txt`, a smaller runtime dependency list for the API service. Full local development and testing dependencies remain in `requirements.txt`.

## Database

Database logic lives in `cairo_transport/database.py`.

- `TransportDB` creates or opens `cairo_transport/cairo_transport.db`.
- `seed_from_data_module()` populates SQLite tables from `cairo_transport/data.py`.
- `build_graph()` rebuilds the in-memory `TransportGraph` from SQLite rows.
- The CLI and API both use the database-backed graph flow.
- In Docker, `CAIRO_TRANSPORT_DB_PATH` points SQLite to `/app/data/cairo_transport.db`, persisted by the `cairo_transport_data` volume.

## API Overview

Main endpoint groups:

- `GET /api/network/summary`
- `GET /api/network/nodes`
- `GET /api/network/edges`
- `GET /api/db/summary`
- `GET /api/db/demand-pairs`
- `GET /api/db/bus-routes`
- `GET /api/db/all-contents`
- `POST /api/algorithms/shortest-path`
- `POST /api/algorithms/emergency-routing`
- `POST /api/algorithms/mst`
- `POST /api/algorithms/bus-allocation`
- `POST /api/algorithms/road-maintenance`
- `POST /api/algorithms/traffic-signals`
- `POST /api/algorithms/memoized-planner`
- `POST /api/algorithms/airport-access`
- `POST /api/simulation/rush-hour`
- `POST /api/simulation/road-closure`
- `POST /api/simulation/new-road-analysis`
- `GET /api/ml/congestion-model`
- `POST /api/ml/predict-congestion`
- `POST /api/visualization/race`

## Algorithms

### Modified Kruskal MST

- Uses Union-Find with path compression and union by rank.
- Sorts existing roads by `distance / condition`.
- Handles mandatory critical nodes such as `F9`, `F10`, and `13`.
- Suggests top candidate roads by `capacity / construction_cost`.
- Complexity: `O(E log E) + O(E alpha(V))`.

### Dijkstra and Time-Aware Routing

- Uses congestion-aware edge weight: `distance * (1 + traffic[time] / capacity)`.
- Supports multiple time slots.
- Supports alternate path discovery under road closures.
- Complexity: `O((V + E) log V)`.

### A* Emergency Routing

- Routes to the nearest facility of the requested type.
- Uses Euclidean distance over node coordinates as the heuristic.
- Applies emergency preemption by reducing effective road weight.
- Complexity: `O(E log V)` average case.

### Dynamic Programming

- Bus allocation uses 0/1 knapsack over route choices.
- Road maintenance uses integer-budget DP over poor-condition roads.
- Memoized route planning caches repeated shortest-path queries.
- Complexity: `O(n * W)` for the knapsack-style modules.

### Greedy Signal Optimization

- Ranks incoming roads by flow-to-capacity ratio.
- Assigns green time proportionally by rank.
- Flags roads above high utilization thresholds.
- Complexity: `O(degree(v) log degree(v))`.

### Machine Learning Congestion Model

The ML module trains a linear regression model from the project traffic data when scikit-learn is installed. It predicts congestion from time of day, flow, capacity, and distance, then compares static formula weights against ML-based route weights.

Run the standalone ML demo with:

```bash
python congestion_ml_script.py
```

## Frontend Scripts

From `frontend/`:

```bash
npm run dev
npm run build
npm run preview
npm run lint
```

## Testing

Run the test suite from the project root:

```bash
pytest tests/ -v
```

The tests cover:

- Algorithm correctness for Dijkstra, A*, MST, DP, and greedy methods.
- Graph structure validation.
- Database integrity.
- Scenario simulations.
- Data validation.

## Generated Output

Network and scenario visualizations are saved under `output/`, including examples such as:

- `full_network.png`
- `shortest_path.png`
- `mst_overlay.png`
- `congestion_morning.png`

## Documentation

See `docs/technical_report.md` for the longer technical report, including architecture, algorithm details, data analysis, evaluation, and references.

## Notes

- Routing uses existing roads by default; candidate roads are used for infrastructure analysis.
- Facility nodes without resident population use fixed plot sizes for visualization.
- `F9` and `F10` are represented for emergency and infrastructure analysis even though the original road list leaves them isolated from the main network.
- The road maintenance requirement combines fractional-knapsack wording with dynamic programming, so this implementation uses integer-budget DP to keep the course focus on DP.
#   C a i r o - T r a n s p o r t 
 
 