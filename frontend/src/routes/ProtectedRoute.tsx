import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore, type Role } from "../store/authStore";

interface ProtectedRouteProps {
  allowedRoles?: Role[];
}

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();
  const role = user?.role;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!role) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    // Redirect securely mapped routes based on authenticated role
    if (role === 'admin') return <Navigate to="/admin" replace />;
    if (role === 'merchant') return <Navigate to="/merchant" replace />;
    return <Navigate to="/user" replace />;
  }

  return <Outlet />;
}
