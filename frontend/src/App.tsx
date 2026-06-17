import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "@/components/Layout";
import Login from "@/features/auth/Login";
import Register from "@/features/auth/Register";
import Dashboard from "@/features/dashboard/Dashboard";
import AiChat from "@/features/ai/AiChat";
import Habits from "@/features/habits/Habits";
import Lists from "@/features/lists/Lists";
import Placeholder from "@/features/Placeholder";
import Pomodoro from "@/features/pomodoro/Pomodoro";
import Projects from "@/features/projects/Projects";
import Settings from "@/features/settings/Settings";
import { useAuth } from "@/store/auth";

function Protected({ children }: { children: ReactNode }) {
  const token = useAuth((s) => s.accessToken);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="lists" element={<Lists />} />
        <Route path="projects" element={<Projects />} />
        <Route path="habits" element={<Habits />} />
        <Route path="calendar" element={<Placeholder title="Calendar" />} />
        <Route path="pomodoro" element={<Pomodoro />} />
        <Route path="ai" element={<AiChat />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
