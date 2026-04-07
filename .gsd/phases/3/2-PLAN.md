---
phase: 3
plan: 2
wave: 2
---

# Plan 3.2: Admin CRUD Endpoints

## Objective
Implement admin management capabilities to create/onboard users and merchants, and list them. These routes will be protected by the `require_role("admin")` dependency.

## Context
- .gsd/SPEC.md
- backend/app/core/security.py (require_role dependency)
- backend/app/schemas/user.py (AdminUserCreateSchema)
- backend/app/schemas/merchant.py (MerchantCreateSchema)

## Tasks

<task type="auto">
  <name>Implement Admin Router</name>
  <files>backend/app/api/admin.py</files>
  <action>
    Create FastAPI router for Admin operations protected by `require_role('admin')`:
    - GET /users: Returns list of UserResponseSchema.
    - POST /users: Accepts AdminUserCreateSchema, creates User. Returns UserResponseSchema. Must enforce unique mobile logic (400 if already exists).
    - GET /merchants: Returns list of MerchantResponseSchema. Ensure joining or mapping to populate `user_name` and `user_mobile` from the User table into the response.
    - POST /merchants: Accepts MerchantCreateSchema. Look up User by `user_mobile`. If user doesn't exist, return 404. Else create Merchant linked to user's id. Returns MerchantResponseSchema (also populated). Ensure 'upi_id' uniqueness constraint correctly handled.
  </action>
  <verify>python -c "from app.api.admin import router; assert '/users' in [r.path for r in router.routes]"</verify>
  <done>Admin router exposes user and merchant creation and listing endpoints.</done>
</task>

<task type="auto">
  <name>Integrate Admin Router</name>
  <files>backend/app/main.py</files>
  <action>
    - Include `admin.router` with prefix `/admin` and tags `["admin"]`.
  </action>
  <verify>python -c "from app.main import app; assert '/admin/users' in [r.path for r in app.routes]"</verify>
  <done>The `/admin` endpoints are active in the FastAPI app.</done>
</task>

## Success Criteria
- [ ] User listing and creation requires admin role
- [ ] Merchant creation verifies associated user mobile
- [ ] Endpoints properly wired into `main.py`
