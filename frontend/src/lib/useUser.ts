import { useQuery } from "@tanstack/react-query";

import api from "./api";

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  locale: string;
  calendar_pref: "gregorian" | "jalali";
  timezone: string;
}

export function useUser() {
  return useQuery<UserProfile>({
    queryKey: ["me"],
    queryFn: async () => (await api.get("/users/me")).data,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}
