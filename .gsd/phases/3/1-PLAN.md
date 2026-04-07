---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Auth API Endpoints

## Objective
Implement OTP authentication endpoints to support login and mock SMS retrieval, and issue JWTs using httpOnly cookies. Also create the `/auth/me` endpoint so the frontend can recover session state. Auto-generate the first OTP for the seeded admin user.

## Context
- .gsd/SPEC.md
- backend/app/core/security.py
- backend/app/schemas/auth.py
- backend/app/db/models.py

## Tasks

<task type="auto">
  <name>Implement Auth Router</name>
  <files>backend/app/api/auth.py</files>
  <action>
    Create FastAPI router for Auth with the following async routes:
    - POST /request-otp: Accepts OtpRequestSchema. Generates 6-digit OTP, creates or updates OtpSession with hashed OTP and plaintext OTP (for demo), sets expiry timestamp based on config.
    - GET /otp-inbox/{mobile}: Retrieves latest plaintext OTP from OtpSession for the mobile (for demo UI). Returns OtpInboxResponseSchema. Return 404 if no recent OTP.
    - POST /verify-otp: Accepts OtpVerifySchema. Retrieves unexpired OtpSession, uses verify_password(), ensures User exists & activates it, mints JWT using create_access_token(). Set cookie with set_auth_cookie(). Returns TokenResponseSchema. Return 401 on failure.
    - POST /logout: Uses clear_auth_cookie() and returns a confirmation message.
    - GET /me: Uses get_current_user dependency to verify token and return UserResponseSchema.
  </action>
  <verify>cd backend && python -c "from app.api.auth import router; assert '/verify-otp' in [r.path for r in router.routes]"</verify>
  <done>Router has all 5 required endpoints correctly scoped.</done>
</task>

<task type="auto">
  <name>Integrate Router and Seed Admin OTP</name>
  <files>backend/app/main.py</files>
  <action>
    - Include `auth.router` with prefix `/auth` and tags `["auth"]`.
    - In `_seed_admin()`, after creating the admin User, generate a mock OTP (e.g., '123456'), hash it, and create an OtpSession for the admin so we can immediately call `/verify-otp`.
  </action>
  <verify>cd backend && python -c "from app.main import app; assert '/auth/me' in [r.path for r in app.routes]"</verify>
  <done>The `/auth` endpoints are active in the app and the admin seeding process includes an initial OTP.</done>
</task>

## Success Criteria
- [ ] /auth/request-otp stores OTP hash and mock plaintext
- [ ] /auth/verify-otp validates OTP and sets access_token cookie
- [ ] /auth/me reads cookie and returns user profile
- [ ] Seed admin function creates an OTP session
