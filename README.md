# Peblo TV Mini

A small, runnable content-management and viewer prototype based on the supplied challenge brief.

## Run locally

```bash
cd backend
python3 -m pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`, `http://localhost:5173` for the CMS, or `http://localhost:5174` for the viewer after starting each Vite app with `npm install && npm run dev` in its directory. Docker users can run `docker compose up --build`.

Demo identities are passed through `X-User`: `admin@example.com` can publish and `editor@example.com` cannot. This is intentionally a take-home authentication simplification, not production identity management.

## Architecture

- `backend/app/main.py` exposes separate admin and public catalogue routes.
- `backend/app/services/catalogue.py` owns validation, deterministic ordering, language grouping fields, season-0 trailer separation, and publication.
- `backend/app/storage.py` defines the storage boundary; `LocalStorage` is the local implementation and can be replaced by an R2 adapter without changing API code.
- `cms` only calls `/admin/*`; `viewer` only calls `/catalog`.

Publishing writes `catalogue-{run}.json` completely, flushes it, then atomically replaces `current.json`. A process crash before the manifest replacement leaves the previous complete catalogue active.

The current prototype uses an in-memory domain store with file-backed catalogue artifacts so it can run without external services. PostgreSQL, Alembic, persisted publish-run history, image upload validation, and the supplied `seed_shows.json`/`reference.json` should be the next implementation slice once those challenge files are available; none were present in the empty workspace. The current validation and publish pipeline intentionally exposes that limitation rather than claiming those features exist.

## Checks

```bash
cd backend
PYTHONPATH=. pytest -q
```

The tests cover health/catalogue availability and API-level editor publish denial. Search, upload validation, database constraints, and full seed validation still need dedicated tests in the production version.