# Plan 3.2: Admin CRUD Endpoints Summary

## Implementation Details
- Created `backend/app/api/admin.py` with endpoints governed by `require_role("admin")`:
  - `GET /users` to list all Users.
  - `POST /users` to create a new User (verifies unique mobile).
  - `GET /merchants` to list all Merchants (denormalizes user data via `selectinload`).
  - `POST /merchants` to create a new Merchant (verifies user mobile and upi_id).
- Main application hook enabled for `admin.router`.

## Verification Passed
- Verified endpoints are loaded in `admin.router`.
- Verified `/admin/users` exists in the application route map.
