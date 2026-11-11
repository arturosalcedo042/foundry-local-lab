# Foundry-inspired local data platform (Windows 11)

Stack: Python 3.11, PySpark 4.2.0, PostgreSQL 17, FastAPI, React 19, Docker Compose.

## Requirements
- Windows 11, Docker Desktop running with Linux containers and WSL 2 backend
- PowerShell terminal; ~6 GB available RAM recommended; Internet for first-time image/package downloads
- No local Java, Python, or Node installation needed

## Start
```powershell
cd foundry-local-lab
docker compose up -d --build
docker compose run --rm etl
```
Open http://localhost:5173 for the React app, http://localhost:8000/docs for API docs.

## Verify data with SQL
```powershell
docker compose exec db psql -U foundry -d foundrylab -c "SELECT COUNT(*) FROM orders;"
docker compose exec db psql -U foundry -d foundrylab -c "SELECT * FROM pipeline_runs;"
```

## Practice
1. Inspect `data/*.csv` (raw datasets).
2. Open `etl/pipeline.py` (data joins, cleaning, payment status).
3. Re-run `docker compose run --rm etl` after editing CSV input. Refresh UI.
4. Change an order status in UI. It is written to PostgreSQL and survives rerunning ETL.
5. Inspect `api/main.py` for operational API actions.
6. Add an extra column (e.g. `risk_level`) throughout ingestion, schema, API and UI.

## Useful troubleshooting
- `docker compose ps` check container status.
- `docker compose logs api` or `docker compose logs frontend` for diagnostics.
- For an ETL error, `docker compose run --rm etl` shows full logs.
- Ports: UI 5173, API 8000, PostgreSQL 5433 (bound to 127.0.0.1).
- If ports are busy, modify host-side ports in `compose.yaml`. Also update `VITE_API_URL` and CORS allowed origins if changing frontend/API ports.
- `docker compose down` stops containers and retains database data.
- `docker compose down -v` deletes the sample database and npm volume (destructive).

## Limits
- The "Ontology" is simulated by relational objects and foreign keys, not a Palantir Ontology.
- This project demonstrates local batch ETL. It does not offer Foundry's governance, branch management, lineage UI, Actions framework, job scheduler, or AIP.
- For learning only: static development credentials and permissive access, no production authentication, no distributed Spark cluster.
- ETL `collect()` is deliberately suitable only for this small dataset. A production system should use distributed loads/JDBC rather than collect data on the driver.
