---
phase: 6
plan: 2
wave: 1
---

# Plan 6.2: Auth Integration & Redirection

## Objective
Wire the login form to the backend FastAPI authentication endpoints and trigger role-based redirection upon success.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md (Phase 6)

## Tasks

<task type="auto">
  <name>Implement Auth API Calls</name>
  <files>frontend/src/pages/Login.tsx</files>
  <action>
    - Integrate `axios` calls bridging `apiClient.post("/auth/request-otp")` targeting the mobile form submission. On success, advance the step state to `'otp'`.
    - Integrate `apiClient.post("/auth/verify-otp")` mapping the incoming OTP code.
    - Manage loading transitions and capture errors triggering `react-hot-toast` alerts.
  </action>
  <verify>grep "verify-otp" frontend/src/pages/Login.tsx</verify>
  <done>Network requests bind directly to backend mechanisms seamlessly.</done>
</task>

<task type="auto">
  <name>Store Hydration and Redirection</name>
  <files>frontend/src/pages/Login.tsx</files>
  <action>
    - During the `verify-otp` success resolution block, extract the user schema from the API response payload.
    - Hit `useAuthStore.getState().setAuth(user)` to hydrate the frontend Zustand instance.
    - Instantiate `useNavigate()`, resolving the authenticated `user.role` natively and traversing the router logic towards `/user`, `/merchant`, or `/admin` correctly based on the payload.
  </action>
  <verify>grep "setAuth" frontend/src/pages/Login.tsx</verify>
  <done>Authentication data hydrates global stores redirecting execution domains accurately.</done>
</task>

## Success Criteria
- [ ] API integrations effectively trigger HTTP flows over backend configurations.
- [ ] Zustand actively recognizes and caches active session bounds structurally.
- [ ] Application strictly directs successful logins towards explicit role mappings cleanly.
