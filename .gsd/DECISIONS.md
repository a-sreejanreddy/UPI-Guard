# DECISIONS.md — Architecture Decision Records

## ADR-001: MLP over CNN for fraud detection
**Date**: Project initialization
**Decision**: Use Dense Neural Network (MLP) instead of CNN
**Rationale**: Transaction features are flat tabular data with no spatial/sequential
structure. MLP is the architecturally correct choice. CNN would require treating features
as a 1D sequence which adds complexity with no accuracy benefit.
**Status**: Accepted

## ADR-002: JWT in httpOnly cookie over localStorage
**Date**: Project initialization
**Decision**: Store JWT in httpOnly, Secure, SameSite=Strict cookie
**Rationale**: localStorage is vulnerable to XSS. httpOnly cookies are inaccessible to
JavaScript, eliminating token theft via script injection.
**Status**: Accepted

## ADR-003: Log ALL transactions including BLOCKED_FRAUD
**Date**: Project initialization
**Decision**: Write every transaction to the DB regardless of fraud outcome
**Rationale**: Blocking DB writes for fraudulent transactions eliminates the audit trail.
Real fraud detection systems require forensic records of all attempts.
**Status**: Accepted

## ADR-004: aiosqlite + SQLAlchemy async over sync SQLite
**Date**: Project initialization
**Decision**: Use aiosqlite with SQLAlchemy 2.0 async engine
**Rationale**: FastAPI is async; using sync DB calls would block the event loop under
concurrent requests.
**Status**: Accepted

## ADR-005: Zustand + TanStack Query over Redux
**Date**: Project initialization
**Decision**: Zustand for auth state, TanStack Query for server state
**Rationale**: Redux is overkill for 3 roles + auth. Zustand is minimal and boilerplate-free.
TanStack Query handles caching, loading states, and refetching natively.
**Status**: Accepted
