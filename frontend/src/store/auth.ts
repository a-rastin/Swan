import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  setToken: (t: string | null) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  setToken: (t) => set({ accessToken: t }),
  logout: () => set({ accessToken: null }),
}));
