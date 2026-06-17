import axios from "axios";

import { useAuth } from "@/store/auth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api/v1",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = useAuth.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, try one refresh then replay.
let refreshing: Promise<string | null> | null = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      refreshing ??= refreshToken();
      const token = await refreshing;
      refreshing = null;
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
      useAuth.getState().logout();
    }
    return Promise.reject(error);
  },
);

async function refreshToken(): Promise<string | null> {
  try {
    const { data } = await axios.post(
      `${import.meta.env.VITE_API_BASE || "/api/v1"}/auth/refresh`,
      {},
      { withCredentials: true },
    );
    useAuth.getState().setToken(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

export default api;
