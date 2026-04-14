import { useState } from "react";
import { useAuthStore } from "../../store/authStore";
import { useNavigate, NavLink } from "react-router-dom";

export function Sidebar() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await logout();
      navigate("/login");
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <aside className="hidden md:flex flex-col p-4 space-y-2 h-screen w-64 bg-surface border-r-0 fixed left-0 top-0 z-50">
      <div className="px-4 py-6 mb-4">
        <span className="text-xl font-black text-tertiary font-headline">UPI Guard</span>
        <p className="text-xs text-on-surface-variant font-medium tracking-wide">Secure Banking</p>
      </div>
      <nav className="flex-1 space-y-2">
        <NavLink 
          to="/user" 
          className={({ isActive }) => 
            `flex items-center gap-3 px-4 py-3 rounded-xl shadow-sm font-headline font-semibold duration-200 ease-in-out ${isActive ? 'bg-surface-container-lowest text-tertiary' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low'}`
          }
        >
          <span className="material-symbols-outlined" data-icon="dashboard">dashboard</span>
          <span>Dashboard</span>
        </NavLink>
      </nav>
      <div className="mt-auto p-4 bg-primary-container rounded-xl overflow-hidden relative group">
        <div className="relative z-10">
          <p className="text-on-primary-container text-xs font-bold mb-2">PRO GUARD ACTIVE</p>
          <p className="text-primary-fixed text-xs opacity-70">Real-time threat monitoring is enabled.</p>
        </div>
      </div>
      <button 
        onClick={handleLogout} 
        disabled={isLoggingOut}
        className="flex items-center gap-3 px-4 py-3 text-on-surface hover:text-tertiary font-headline font-semibold text-left disabled:opacity-50 transition-opacity"
      >
          <span className="material-symbols-outlined" data-icon="logout">logout</span>
          <span>{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
      </button>
    </aside>
  );
}
