import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Role = "admin" | "merchant" | "user";

export interface User {
  id: number;
  name: string;
  mobile: string;
  role: Role;
}

interface AuthState {
  user: User | null;
  role: Role | null;
  isAuthenticated: boolean;
  setAuth: (user: User, role: Role) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      role: null,
      isAuthenticated: false,
      setAuth: (user, role) => set({ user, role, isAuthenticated: true }),
      logout: () => set({ user: null, role: null, isAuthenticated: false }),
    }),
    {
      name: "auth-storage",
    }
  )
);
