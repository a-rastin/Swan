import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import TaskList from "@/features/tasks/TaskList";
import api from "@/lib/api";
import { useUser } from "@/lib/useUser";

interface Project {
  id: string;
  name: string;
  description?: string | null;
  color?: string | null;
  status: string;
  start_date?: string | null;
  due_date?: string | null;
}

const STATUS_CYCLE: Record<string, string> = {
  active: "done",
  done: "archived",
  archived: "active",
};

export default function Projects() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: user } = useUser();
  const [newName, setNewName] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const calendarPref = user?.calendar_pref ?? "gregorian";
  const locale = user?.locale ?? "en";

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => (await api.get("/projects")).data,
  });

  const add = useMutation({
    mutationFn: async (name: string) => (await api.post("/projects", { name })).data,
    onSuccess: () => {
      setNewName("");
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const cycleStatus = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) =>
      api.patch(`/projects/${id}`, { status: STATUS_CYCLE[status] ?? "active" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/projects/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });

  const statusBadge = (s: string) => {
    const colors: Record<string, string> = {
      active: "bg-green-100 text-green-700",
      done: "bg-blue-100 text-blue-700",
      archived: "bg-gray-100 text-gray-500",
    };
    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          cycleStatus.mutate({ id: projects.find((p) => p.status === s)?.id ?? "", status: s });
        }}
        className={`rounded px-2 py-0.5 text-xs ${colors[s] ?? ""}`}
      >
        {t(`project.status.${s}`)}
      </button>
    );
  };

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.projects")}</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (newName.trim()) add.mutate(newName.trim());
        }}
        className="mb-4 flex gap-2"
      >
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder={t("project.name")}
          className="flex-1 rounded border px-3 py-2 text-sm"
        />
        <button className="rounded bg-sky-600 px-3 py-2 text-sm text-white">
          {t("project.add")}
        </button>
      </form>

      {projects.length === 0 ? (
        <p className="text-sm text-gray-500">{t("project.empty")}</p>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <div key={p.id} className="rounded border bg-white">
              <div
                className="flex cursor-pointer items-center gap-2 px-3 py-2"
                onClick={() => setExpanded(expanded === p.id ? null : p.id)}
              >
                <span className="flex-1 font-medium">{p.name}</span>

                {/* status badge — click cycles status without expanding */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    cycleStatus.mutate({ id: p.id, status: p.status });
                  }}
                  className={`rounded px-2 py-0.5 text-xs ${
                    p.status === "active"
                      ? "bg-green-100 text-green-700"
                      : p.status === "done"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {t(`project.status.${p.status}`)}
                </button>

                <span className="text-gray-400">{expanded === p.id ? "▲" : "▼"}</span>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    remove.mutate(p.id);
                  }}
                  className="text-sm text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>

              {expanded === p.id && (
                <div className="border-t px-3 py-3">
                  {p.description && (
                    <p className="mb-2 text-sm text-gray-500">{p.description}</p>
                  )}
                  <TaskList
                    queryKey={["tasks", "project", p.id]}
                    projectId={p.id}
                    calendarPref={calendarPref}
                    locale={locale}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
