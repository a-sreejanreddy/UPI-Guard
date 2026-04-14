---
phase: 6
plan: 1
wave: 1
---

# Plan 6.1: Authentication UI Foundation

## Objective
Build the client-side login views including the multi-step form and the simulated SMS Inbox panel.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md (Phase 6)

## Tasks

<task type="auto">
  <name>Build Login Page Skeleton</name>
  <files>frontend/src/pages/Login.tsx, frontend/src/App.tsx</files>
  <action>
    - Create `frontend/src/pages/Login.tsx`.
    - Implement a two-step standard React component layout avoiding complex routing. State should track `step: 'mobile' | 'otp'` and the `mobileNumber` entered.
    - Set up `react-hook-form` with `zod` schema to validate the 10-digit mobile number layout.
    - Update `App.tsx` replacing the dummy `<LoginPlaceholder />` with the exported `Login` page.
  </action>
  <verify>grep "Login" frontend/src/App.tsx</verify>
  <done>Login component scaffolding routes naturally over the root index layout.</done>
</task>

<task type="auto">
  <name>Build SMS Inbox Panel</name>
  <files>frontend/src/components/SMSInboxPanel.tsx, frontend/src/pages/Login.tsx</files>
  <action>
    - Create `frontend/src/components/SMSInboxPanel.tsx`.
    - This component accepts a `mobile` prop. Utilize `@tanstack/react-query` to hit `GET /auth/otp-inbox/{mobile}` with a `refetchInterval` of 3000ms.
    - Style the visual container to simulate a mobile text notification bubble floating on the side or bottom.
    - Place the `<SMSInboxPanel>` into the `Login.tsx` view only when the `step` is `'otp'`.
  </action>
  <verify>grep "useQuery" frontend/src/components/SMSInboxPanel.tsx</verify>
  <done>The SMS simulation pane accurately queries backend OTP endpoints when active.</done>
</task>

## Success Criteria
- [ ] Login screen actively toggles between mobile and OTP input steps structurally.
- [ ] Zod schema effectively blocks invalid mobile digits visually.
- [ ] SMS Inbox Panel successfully leverages TanStack polling.
