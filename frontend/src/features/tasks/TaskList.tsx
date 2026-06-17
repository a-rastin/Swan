import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";
import type { CalendarPref } from "@/lib/date";
import { formatDate } from "@/lib/date";
import TaskDetail, { type Task } from "./TaskDetail";

interface Props {
  queryKey: string[];
  params?: Record<string, string>;
  calendarPref: CalendarPref;
  locale: string;
  listId?: string;
  projectId?: string;
}

const PRIORITY_COLORS = ["", "text-blue-500", "text-yellow-500", "text-red-500"];
const PRIORITY_ICONS  = ["", "↑", "↑↑", "↑↑↑"];

export default function TaskList({ queryKey, params = {}, calendarPref, locale, listId, projectId }: Props) {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language === "fa";
  const qc = useQueryClient();

  const [newTitle, setNewTitle] = useState("");
  const [selected, setSelected] = useState<Task | null>(null);

  const qs = new URLSearchParams(params);
  if (listId) qs.set("list_id", listId);
  if (projectId) qs.set("project_id", projectId);

  const { data: tasks = [] } = useQuery<Task[]>({
    queryKey,
    queryFn: async () => (await api.get(`/tasks?${qs}`)).data,
  });

  const add = useMutation({
    mutationFn: async (title: string) =>
      (await api.post("/tasks", { title, list_id: listId ?? null, project_id: projectId ?? null })).data,
    onSuccess: () => {
      setNewTitle("");
      qc.invalidateQueries({ queryKey });
    },
  });

  const complete = useMutation({
    mutationFn: async (id: string) => api.post(`/tasks/${id}/complete`),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (newTitle.trim()) add.mutate(newTitle.trim());
        }}
        className="mb-3 flex gap-2"
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder={t("task.title")}
          className="flex-1 rounded border px-3 py-2 text-sm"
        />
        <button className="rounded bg-sky-600 px-3 py-2 text-sm text-white">
          {t("task.add")}
        </button>
      </form>

      {tasks.length === 0 ? (
        <p className="text-sm text-gray-500">{t("task.empty")}</p>
      ) : (
        <ul className="space-y-1">
          {tasks.map((task) => (
            <li
              key={task.id}
              className="flex items-center gap-2 rounded border bg-white px-3 py-2"
            >
              <input
                type="checkbox"
                checked={task.status === "done"}
                onChange={() => complete.mutate(task.id)}
                className="shrink-0"
              />
              <button
                onClick={() => setSelected(task)}
                className="flex-1 text-start"
              >
                <span className={task.status === "done" ? "text-gray-400 line-through" : ""}>
                  {task.title}
                </span>
                {task.priority > 0 && (
                  <span className={`ms-2 text-xs ${PRIORITY_COLORS[task.priority]}`}>
                    {PRIORITY_ICONS[task.priority]}
                  </span>
                )}
                {task.due_at && (
                  <span className="ms-2 text-xs text-gray-400">
                    {formatDate(task.due_at, calendarPref, locale)}
                  </span>
                )}
                {task.recurrence_rrule && (
                  <span className="ms-2 text-xs text-sky-400">↻</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <TaskDetail
          task={selected}
          invalidateKey={queryKey}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
