# UPI Guard - Frontend

This is the simulated frontend interface for the UPI Guard Real-Time Fraud Detection System.
It provides user, merchant, and admin dashboards with real-time UI reactions to the MLP fraud engine.

## Environment Variables
Create a `.env` file in this directory based on `.env.example` (or set the following):

```env
VITE_API_URL=http://localhost:8000
```
- **VITE_API_URL:** The backend FastAPI base URL. The frontend Axios client will reject requests in production if this is unset.

## Backend Expectations
- The backend (`http://localhost:8000`) must be running and have the `/auth/logout` endpoint implemented.
- Authentication utilizes `httpOnly` cookies over CORS.
- Role-based capabilities are defined by the backend JWT payload.

## Scripts

### Development Server
```bash
npm install
npm run dev
```

### Build for Production
```bash
npm run build
```

### Linting / Quality
```bash
npm run lint
```
