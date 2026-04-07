import { create } from "zustand";
import { persist } from "zustand/middleware";
import apiClient from "../api/client";

export type Role = "admin" | "merchant" | "user";

export interface User {
  id: number;
  name: string;
  mobile: string;
  role: Role;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (user: User) => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setAuth: (user) => set({ user, isAuthenticated: true }),
      logout: async () => {
        try {
          await apiClient.post("/auth/logout");
        } catch (error) {
          console.error("Logout failed:", error);
        } finally {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: "auth-storage",
    }
  )
);
