import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";
import { useUser } from "@/lib/useUser";
import TaskList from "@/features/tasks/TaskList";

interface ListItem {
  id: string;
  name: string;
  color?: string;
}

export default function Lists() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: user } = useUser();
  const [newName, setNewName] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const calendarPref = user?.calendar_pref ?? "gregorian";
  const locale = user?.locale ?? "en";

  const { data: lists = [] } = useQuery<ListItem[]>({
    queryKey: ["lists"],
    queryFn: async () => (await api.get("/lists")).data,
  });

  const add = useMutation({
    mutationFn: async (name: string) => (await api.post("/lists", { name })).data,
    onSuccess: () => {
      setNewName("");
      qc.invalidateQueries({ queryKey: ["lists"] });
    },
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/lists/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lists"] }),
  });

  return (
    <div className="max-w-xl">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.lists")}</h1>

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
          placeholder={t("nav.lists")}
          className="flex-1 rounded border px-3 py-2 text-sm"
        />
        <button className="rounded bg-sky-600 px-3 py-2 text-sm text-white">+</button>
      </form>

      <div className="space-y-2">
        {lists.map((l) => (
          <div key={l.id} className="rounded border bg-white">
            <div className="flex items-center justify-between px-3 py-2">
              <button
                onClick={() => setExpanded(expanded === l.id ? null : l.id)}
                className="flex-1 text-start font-medium"
              >
                {l.name} {expanded === l.id ? "▲" : "▼"}
              </button>
              <button
                onClick={() => remove.mutate(l.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
            {expanded === l.id && (
              <div className="border-t px-3 py-3">
                <TaskList
                  queryKey={["tasks", "list", l.id]}
                  listId={l.id}
                  calendarPref={calendarPref}
                  locale={locale}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
