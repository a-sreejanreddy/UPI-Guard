---
phase: 5
plan: 3
wave: 2
---

# Plan 5.3: Core Routing and Baseline Layout

## Objective
Organize routes, layout scaffolds, and protect them utilizing auth role checks. Build generic UX utilities such as the LoadingSpinner.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md

## Tasks

<task type="auto">
  <name>Protected Route Component</name>
  <files>frontend/src/routes/ProtectedRoute.tsx</files>
  <action>
    - Ensure directory `frontend/src/routes` exists.
    - Read `isAuthenticated` and `role` from the Zustand `useAuthStore`.
    - Accept an optional `allowedRoles` array prop.
    - Redirect unauthenticated users strictly to `/login`.
    - Redirect unauthorized authenticated users (e.g. `User` visiting `/admin`) to their respective default dashboard (`/user`, `/admin`, `/merchant`).
    - Render `<Outlet />` or `children` cleanly on successful verification.
  </action>
  <verify>cat frontend/src/routes/ProtectedRoute.tsx | grep Navigate</verify>
  <done>Role-restrictive boundaries securely and seamlessly apply to wrapped pages natively.</done>
</task>

<task type="auto">
  <name>Layout and Components Foundation</name>
  <files>
    frontend/src/components/Layout.tsx,
    frontend/src/components/Navbar.tsx,
    frontend/src/components/LoadingSpinner.tsx
  </files>
  <action>
    - Form a standard `Layout` mapping a top fixed `Navbar` and a `<main>` flex container structure for incoming pages.
    - Setup `Navbar` tracking the global store: show Login if logged out, or show role-specific Nav links (e.g. "Merchant Dashboard" if role is merchant) and a Logout button hooking into `authStore.logout()`.
    - Build a generic animated Tailwind spin element (`LoadingSpinner`) for loading states utilizing the `lucide-react` `Loader2` or pure CSS ring.
  </action>
  <verify>cat frontend/src/components/Layout.tsx | grep Navbar</verify>
  <done>Global interface layout elements consistently orchestrate atop underlying Vite routing context rendering the main frame.</done>
</task>

<task type="auto">
  <name>Define Application Route Tree</name>
  <files>frontend/src/App.tsx</files>
  <action>
    - Overhaul App.tsx to instantiate the primary React Router `<Routes>` blocks referencing the overarching `Layout`.
    - Map base path `/` logically to a standalone Home landing page or trigger an immediate contextual Redirect.
    - Map `/login` out to a placeholder static element.
    - Envelop `/user`, `/merchant`, and `/admin` boundaries tightly with `<ProtectedRoute>` corresponding roles mapped.
  </action>
  <verify>cat frontend/src/App.tsx | grep Routes</verify>
  <done>Primary application navigation matrix definitively locks endpoints avoiding unauthorized URL hijacking.</done>
</task>

## Success Criteria
- [ ] Route guarding ensures effectively isolated execution logic protecting disparate data endpoints mapping logic.
- [ ] Dynamic Layout Navigation effectively evaluates the cached user state, reflecting authenticated entity bounds dynamically.
- [ ] The core architecture gracefully encapsulates Vite within a single isolated component container mapping DOM flows successfully.
