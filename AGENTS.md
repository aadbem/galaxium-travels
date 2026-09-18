# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Structure

Monorepo with two independent sub-projects under `galaxium-travels/`:
- `booking_system_backend/` — Python FastAPI + FastMCP, SQLite via SQLAlchemy
- `booking_system_frontend/` — React 19 + TypeScript + Vite + Tailwind CSS

Start both: `./start.sh` from `galaxium-travels/` (manages venv + npm automatically).

## Backend Commands

All commands must be run from `booking_system_backend/` with the venv activated:

```bash
source .venv/bin/activate
uvicorn server:app --reload --port 8080   # dev server
python server.py                          # prod-style run
pytest                                    # all tests
pytest tests/test_services.py::TestBookingService::test_book_flight_success  # single test
pytest -k "test_register_user"            # by keyword
```

- Tests use an **in-memory SQLite** database (not the `booking.db` file). The `conftest.py` patches `SessionLocal` and suppresses `seed()` for every test run.
- Backend imports are **flat** (no package prefix): `from models import ...`, `from services import booking`. This works because `conftest.py` does `sys.path.insert(0, parent)` — do not add `booking_system_backend` as a package.

## Frontend Commands

All commands must be run from `booking_system_frontend/`:

```bash
npm run dev     # dev server on :5173
npm run build   # tsc -b && vite build
npm run lint    # eslint
```

Frontend connects to `VITE_API_URL` (default: `http://localhost:8080`). Copy `.env.example` → `.env` to override.

## Key Patterns

### Backend — service functions return `ErrorResponse`, not exceptions
Service functions (`services/booking.py`, `services/user.py`, `services/flight.py`) return `ErrorResponse` on failure instead of raising exceptions. REST endpoints return the union type directly; MCP tools must check `isinstance(result, ErrorResponse)` and `raise Exception(result.details or result.error)` to propagate errors.

### Backend — Pydantic schemas use `model_validate()` for ORM conversion
All `*Out` schemas have `class Config: from_attributes = True`. Return ORM objects via `BookingOut.model_validate(obj)`, not `BookingOut.from_orm(obj)` (old API).

### Backend — Seat class is a separate table (`FlightSeatClass`)
Valid seat class values: `economy`, `executive`, `galaxium`. Booking/cancelling a seat decrements/increments `FlightSeatClass.seats_available` — **not** `Flight.seats_available`. `Flight.seats_available` is a legacy/summary field.

### Backend — FastMCP is mounted inside FastAPI at `/mcp`
`mcp_app = mcp.http_app()` must be created **before** the FastAPI `app` is instantiated (lifespan ordering). The MCP server is mounted with `app.mount("/mcp", mcp_app)`.

### Frontend — all types mirror backend schemas exactly
`src/types/index.ts` is the single source of truth for shared types. `SeatClass` is a union type `'economy' | 'executive' | 'galaxium'`. Do not use plain `string` for seat class parameters.

### Frontend — API errors are typed via `isErrorResponse()`
`src/services/api.ts` exports `isErrorResponse(response)` which checks `response.success === false`. Use this guard instead of `instanceof` checks when handling `T | ErrorResponse` returns.

### Frontend — user state persisted under key `'galaxium_user'` in localStorage
`useUser` hook (in `src/hooks/useUser.tsx`) reads/writes this key. The `UserProvider` must wrap the entire app — it is already placed at the top of `App.tsx`.

## Database

SQLite file `booking.db` lives in `booking_system_backend/`. Seeded fresh on every server startup via `seed()` called in the FastAPI lifespan — **existing data is wiped on restart**.
