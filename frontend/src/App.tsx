import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./routes/ProtectedRoute";

function LoginPlaceholder() {
  return <div className="text-center p-8 text-xl">Login Page (Coming Soon)</div>;
}

function DashboardPlaceholder({ title }: { title: string }) {
  return <div className="text-center p-8 text-xl">{title} Dashboard (Coming Soon)</div>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPlaceholder />} />
      <Route element={<Layout />}>
        {/* Protected User Routes */}
        <Route element={<ProtectedRoute allowedRoles={['user']} />}>
          <Route path="/user" element={<DashboardPlaceholder title="User" />} />
        </Route>
        
        {/* Protected Merchant Routes */}
        <Route element={<ProtectedRoute allowedRoles={['merchant']} />}>
          <Route path="/merchant" element={<DashboardPlaceholder title="Merchant" />} />
        </Route>

        {/* Protected Admin Routes */}
        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          <Route path="/admin" element={<DashboardPlaceholder title="Admin" />} />
        </Route>
        
        {/* Fallback routing */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
