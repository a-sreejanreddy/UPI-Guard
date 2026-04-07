import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import apiClient from "../api/client";

export function Navbar() {
  const { isAuthenticated, role, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Force local logout even if server fails
    } finally {
      logout();
      navigate("/login");
    }
  };

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex-shrink-0 font-bold text-xl text-blue-600">
            UPI Guard
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {role === "admin" && <span className="text-sm font-medium">Admin Dashboard</span>}
                {role === "merchant" && <span className="text-sm font-medium">Merchant Dashboard</span>}
                {role === "user" && <span className="text-sm font-medium">User Dashboard</span>}
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 border rounded text-sm hover:bg-gray-50 text-gray-700"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login" className="px-3 py-2 border rounded text-sm hover:bg-gray-50 text-gray-700">
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
