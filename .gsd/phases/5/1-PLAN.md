---
phase: 5
plan: 1
wave: 1
---

# Plan 5.1: Scaffold Vite Project & Dependencies

## Objective
Bootstrap the React 18 + Vite frontend with TypeScript, configure Tailwind CSS, and install all required frontend packages.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md

## Tasks

<task type="auto">
  <name>Create Vite Project & Configure Tailwind</name>
  <files>frontend/package.json, frontend/tailwind.config.js, frontend/src/index.css</files>
  <action>
    - Ensure you are in the root directory.
    - Run `npx -y create-vite@latest frontend --template react-ts`.
    - Go into `frontend` and install frontend dependencies using `npm install`.
    - Install Tailwind CSS: `npm install -D tailwindcss postcss autoprefixer` and initialize it (`npx tailwindcss init -p`).
    - Configure Tailwind via `tailwind.config.js` to scan `./src/**/*.{js,ts,jsx,tsx}`.
    - Setup Tailwind directives (`@tailwind base; @tailwind components; @tailwind utilities;`) into `src/index.css`.
    - Remove boilerplate assets/CSS that Vite generates (e.g., App.css, App.tsx cleanup).
  </action>
  <verify>cd frontend && npm list react && npx tailwindcss -h</verify>
  <done>Vite is scaffolded, Tailwind config is present, and index.css has @tailwind directives.</done>
</task>

<task type="auto">
  <name>Install Core Dependencies</name>
  <files>frontend/package.json</files>
  <action>
    - Navigate to `frontend`.
    - Install core routing and state: `npm install react-router-dom zustand @tanstack/react-query axios`
    - Install forms and validation: `npm install react-hook-form @hookform/resolvers zod`
    - Install UI elements: `npm install qrcode.react react-hot-toast lucide-react`
    - Install types: `npm install -D @types/qrcode.react`
  </action>
  <verify>cd frontend && npm list react-router-dom zustand axios</verify>
  <done>All package dependencies specified in ROADMAP are recorded in package.json.</done>
</task>

## Success Criteria
- [ ] `frontend` directory exists with a React-TS Vite project.
- [ ] Tailwind CSS is fully styled and initialized.
- [ ] `package.json` contains modern React ecosystem libraries.
