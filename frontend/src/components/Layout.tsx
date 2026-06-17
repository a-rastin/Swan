import { useTranslation } from "react-i18next";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import api from "@/lib/api";
import { useAuth } from "@/store/auth";

const NAV = ["", "lists", "projects", "habits", "calendar", "pomodoro", "ai", "settings"] as const;
const NAV_KEY: Record<string, string> = {
  "": "dashboard",
  lists: "lists",
  projects: "projects",
  habits: "habits",
  calendar: "calendar",
  pomodoro: "pomodoro",
  ai: "ai",
  settings: "settings",
};

export default function Layout() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const logout = useAuth((s) => s.logout);

  const toggleLang = () => i18n.changeLanguage(i18n.language === "fa" ? "en" : "fa");

  const doLogout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      /* ignore */
    }
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen">
      <aside className="w-52 shrink-0 border-e bg-white p-3">
        <div className="mb-4 px-2 text-lg font-semibold">{t("app.name")}</div>
        <nav className="space-y-1">
          {NAV.map((path) => (
            <NavLink
              key={path}
              to={`/${path}`}
              end={path === ""}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${isActive ? "bg-sky-100 text-sky-700" : "hover:bg-gray-100"}`
              }
            >
              {t(`nav.${NAV_KEY[path]}`)}
            </NavLink>
          ))}
        </nav>
        <div className="mt-4 space-y-2 border-t pt-3">
          <button onClick={toggleLang} className="w-full rounded px-3 py-2 text-sm hover:bg-gray-100">
            {i18n.language === "fa" ? "English" : "فارسی"}
          </button>
          <button onClick={doLogout} className="w-full rounded px-3 py-2 text-start text-sm text-red-600 hover:bg-red-50">
            {t("auth.logout")}
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
