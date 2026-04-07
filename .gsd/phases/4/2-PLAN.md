---
phase: 4
plan: 2
wave: 2
---

# Plan 4.2: Audit Logs, User History & Admin Override

## Objective
Finalize Phase 4 by equipping authenticated Users/Merchants with historical payment oversight, and supplying Administrators an elevated capability to scrutinize model behavior (the 10-feature audit) and manually override inference blockage.

## Context
- .gsd/ROADMAP.md
- backend/app/api/transactions.py
- backend/app/api/admin.py

## Tasks

<task type="auto">
  <name>Build User and Merchant Payment History Queries</name>
  <files>backend/app/api/transactions.py</files>
  <action>
    - Create `GET /my`: Filter active DB user `transactions`, order sequentially `created_at.desc()`.
    - Create `GET /merchant/{merchant_id}`: Require `require_role('merchant')`. Ensure current authorized user actually owns this `merchant_id` (via `merchant.user_id == current_user.id`), fetch all transactions addressed exclusively to this `merchant_id`.
    - Use `selectinload` for denormalized relationship mappings (merchant upi/name + user name).
  </action>
  <verify>cd backend && python -c "from app.api.transactions import router; paths = [r.path for r in router.routes]; assert '/my' in paths and '/merchant/{merchant_id}' in paths"</verify>
  <done>User and Merchant roles support robust querying capability.</done>
</task>

<task type="auto">
  <name>Build Admin Central Audit and Overrides</name>
  <files>backend/app/api/admin.py</files>
  <action>
    - Add `GET /transactions` querying all DB transactions (with limits/offsets pagination, relationships mapped `selectinload`). Return `List[TransactionResponseSchema]`.
    - Add `POST /transactions/{id}/override`: Recover `Transaction` instance by path parameter ID.
    - Override logic: only process when `status == BLOCKED_FRAUD`. Reassign `status` to `ADMIN_OVERRIDDEN`, update `override_by_admin_id` and `override_at` to the current utcnow timestamps. Return `OverrideResponseSchema`.
  </action>
  <verify>cd backend && python -c "from app.api.admin import router; paths = [r.path for r in router.routes]; assert '/transactions' in paths and '/transactions/{id}/override' in paths"</verify>
  <done>Admin has elevated full visibility logic alongside critical fallback authority to approve locked anomalies.</done>
</task>

## Success Criteria
- [ ] Fraud-blocked users can successfully receive manual un-locks
- [ ] Read-operations faithfully restrict exposure across hierarchy
