import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { Login } from "./pages/Login";
import { UserDashboard } from "./pages/UserDashboard";
import { Toaster } from "react-hot-toast";

function DashboardPlaceholder({ title }: { title: string }) {
  return <div className="text-center p-8 text-xl">{title} Dashboard (Coming Soon)</div>;
}

function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* User Dashboard replaces Layout entirely to match the full screen Dashboard UI from Stitch */}
        <Route element={<ProtectedRoute allowedRoles={['user']} />}>
            <Route path="/user" element={<UserDashboard />} />
        </Route>

        <Route element={<Layout />}>
          {/* Protected Merchant Routes */}
          <Route element={<ProtectedRoute allowedRoles={['merchant']} />}>
            <Route path="/merchant" element={<DashboardPlaceholder title="Merchant" />} />
          </Route>

          {/* Protected Admin Routes */}
          <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
            <Route path="/admin" element={<DashboardPlaceholder title="Admin" />} />
          </Route>
        </Route>
        
        {/* Fallback routing */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
