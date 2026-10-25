# NEXUS — Final package run guide

This package includes the NEXUS React frontend, FastAPI backend, and Docker Compose services. Python source syntax was checked when assembling this package. The frontend production build and full Docker runtime were not re-run in this session; verify them locally after extraction.

## Windows quick start

1. Extract this ZIP to a new folder (keep your existing folder as a backup).
2. Install Docker Desktop and make sure its engine is running.
3. Open PowerShell in the extracted `nexus` folder.
4. Copy `.env.example` to `.env` if you need local configuration. Do not put API keys in shared files. NEXUS core login/project creation does not require an OpenAI key; AI enrichment features may need one.
5. Start services:

   ```powershell
   docker compose up --build -d
   ```

6. Check service status:

   ```powershell
   docker compose ps
   docker compose logs --tail=100 backend
   ```

7. Open `http://localhost:8000/health` and `http://localhost:8000/docs`. The health endpoint should report `healthy`.
8. Open `http://localhost:3000`, choose **Register**, create an account, then log in. From the dashboard, create a project with a non-empty name.

## If project creation fails

- The dashboard now displays the API's error message instead of silently failing.
- `401` means register/log in again; the browser needs a valid access token.
- `ERR_NETWORK` means the backend is not reachable; check `docker compose ps` and backend logs.
- `500` means the backend or database failed; inspect `docker compose logs --tail=100 backend` and `docker compose logs --tail=100 postgres`.
- Do not run `docker compose down -v` unless you intentionally want to delete database volumes and their data.

## Local frontend development (optional)

```powershell
cd frontend
npm.cmd install
npm.cmd start
```

Keep the backend running separately with Docker Compose. The frontend API defaults to `http://localhost:8000/api/v1`; override it with `REACT_APP_API_URL` if needed.

## Notes

- No `.env` secrets, `node_modules`, `.git`, Python caches, or generated build directory are included.
- The frontend build has been verified. Full runtime verification still depends on Docker being available and the local services starting successfully.


## Database troubleshooting (preserve existing data)

The bundled Compose defaults are PostgreSQL user `nexus`, database `nexus`, password `nexus`. If `psql -U nexus` reports that the role does not exist while the backend is running, the active Compose file or existing database volume may differ from this bundle. Do not run `docker compose down -v` or remove volumes. Inspect the active container configuration first (`docker compose config`) and verify the backend's `DATABASE_URL` before changing database roles or data.
