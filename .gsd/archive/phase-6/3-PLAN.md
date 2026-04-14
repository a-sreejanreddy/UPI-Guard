---
phase: 6
plan: 3
wave: 2
---

# Plan 6.3: User Dashboard & Payment Interface

## Objective
Construct the core user dashboard view and implement the transaction payment form tying directly into the MLP-backed endpoints.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md (Phase 6)

## Tasks

<task type="auto">
  <name>Build User Dashboard Layout</name>
  <files>frontend/src/pages/UserDashboard.tsx, frontend/src/App.tsx</files>
  <action>
    - Create `frontend/src/pages/UserDashboard.tsx`.
    - Instantiate the top-level structural layout, projecting a welcome header binding `user.name` loaded statically from `useAuthStore`.
    - Configure CSS grids/flex patterns effectively dropping placeholders for the Payment Form and Transaction History sections logically.
    - Wire `UserDashboard.tsx` cleanly extending the placeholder inside `frontend/src/App.tsx` mapped to `/user`.
  </action>
  <verify>grep "UserDashboard" frontend/src/App.tsx</verify>
  <done>User layout skeleton integrates cleanly referencing overarching user states explicitly.</done>
</task>

<task type="auto">
  <name>Implement Payment Submission Interface</name>
  <files>frontend/src/pages/UserDashboard.tsx</files>
  <action>
    - Formulate the `PaymentForm` structure internally containing inputs for specific `merchant_upi` string patterns and `amount` boundaries.
    - Execute a `@tanstack/react-query` `useMutation` structure to `POST /transactions/pay`.
    - Apply validation over payload variables.
    - Handle `APPROVED` payloads displaying a robust `toast.success` modal outputting successful routing confirmation.
  </action>
  <verify>grep "useMutation" frontend/src/pages/UserDashboard.tsx</verify>
  <done>Payment mechanisms orchestrate structural calls directing valid monetary vectors directly.</done>
</task>

## Success Criteria
- [ ] User context maps directly presenting profile metrics cleanly.
- [ ] Merchant input structures isolate payload targets aggressively safely executing React querying forms.
- [ ] APPROVED transactions resolve structurally projecting success validations immediately.
