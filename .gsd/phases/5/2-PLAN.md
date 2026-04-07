---
phase: 5
plan: 2
wave: 1
---

# Plan 5.2: State Management and API Setup

## Objective
Establish the foundational Zustand auth store and the Axios API client configured to communicate with the FastAPI backend over cross-origin.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md

## Tasks

<task type="auto">
  <name>Create Axios Client</name>
  <files>frontend/src/api/client.ts</files>
  <action>
    - Create an Axios instance with `baseURL` derived from an environment variable (`import.meta.env.VITE_API_URL`) or falling back to `http://localhost:8000`.
    - Set `withCredentials: true` critical for the backend's JWT httpOnly cookies.
    - Export the configured instance.
  </action>
  <verify>cat frontend/src/api/client.ts | grep withCredentials</verify>
  <done>Axios client instantiated securely mapping to the local backend port 8000.</done>
</task>

<task type="auto">
  <name>Setup Zustand Auth Store</name>
  <files>frontend/src/store/authStore.ts</files>
  <action>
    - Create a Zustand store tracking `user` object (id, name, mobile, role), `isAuthenticated` boolean, and specific `role` enum context.
    - Expose `setAuth(user, role)` and `logout()` actions resetting the state block.
    - Use `persist` middleware to back up the authentication state tightly into `localStorage`, so users survive page refreshes.
  </action>
  <verify>cat frontend/src/store/authStore.ts | grep persist</verify>
  <done>Global auth tracking acts as single-source-of-truth via Zustand.</done>
</task>

<task type="auto">
  <name>Wrap Application Providers</name>
  <files>frontend/src/main.tsx</files>
  <action>
    - Import QueryClient and QueryClientProvider from `@tanstack/react-query`.
    - Create a standard QueryClient instance (e.g. `staleTime: 30000`).
    - Import BrowserRouter from `react-router-dom`.
    - Wrap the `<App />` component in both `QueryClientProvider` and `BrowserRouter`.
  </action>
  <verify>cat frontend/src/main.tsx | grep QueryClientProvider</verify>
  <done>React root rendered gracefully injecting network querying and routing contexts over App children.</done>
</task>

## Success Criteria
- [ ] Axios client constructed using withCredentials payload transmission natively.
- [ ] Zustand store seamlessly writes and hydrates session state against localStorage constraints.
- [ ] The global `main.tsx` mounts TanStack Query + Router Context architectures.
