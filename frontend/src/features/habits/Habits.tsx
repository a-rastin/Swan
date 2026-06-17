import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";

interface Habit {
  id: string;
  name: string;
  color?: string | null;
  schedule: string;
  today_completed: boolean;
  streak: number;
}

const SCHEDULE_OPTIONS = [
  { value: "daily",    en: "Daily",    fa: "روزانه" },
  { value: "weekdays", en: "Weekdays", fa: "روزهای کاری" },
  { value: "weekly",   en: "Weekly",   fa: "هفتگی" },
];

export default function Habits() {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language === "fa";
  const qc = useQueryClient();

  const [newName, setNewName] = useState("");
  const [newSchedule, setNewSchedule] = useState("daily");

  const { data: habits = [] } = useQuery<Habit[]>({
    queryKey: ["habits"],
    queryFn: async () => (await api.get("/habits")).data,
  });

  const add = useMutation({
    mutationFn: async () =>
      (await api.post("/habits", { name: newName.trim(), schedule: newSchedule })).data,
    onSuccess: () => {
      setNewName("");
      qc.invalidateQueries({ queryKey: ["habits"] });
    },
  });

  const toggleLog = useMutation({
    mutationFn: async (id: string) => (await api.post(`/habits/${id}/log`, {})).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/habits/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });

  const scheduleLabel = (s: string) => {
    const opt = SCHEDULE_OPTIONS.find((o) => o.value === s);
    return opt ? (isFa ? opt.fa : opt.en) : s;
  };

  return (
    <div className="max-w-xl">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.habits")}</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (newName.trim()) add.mutate();
        }}
        className="mb-4 flex gap-2"
      >
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder={t("habit.name")}
          className="flex-1 rounded border px-3 py-2 text-sm"
        />
        <select
          value={newSchedule}
          onChange={(e) => setNewSchedule(e.target.value)}
          className="rounded border px-2 py-2 text-sm"
        >
          {SCHEDULE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {isFa ? o.fa : o.en}
            </option>
          ))}
        </select>
        <button className="rounded bg-sky-600 px-3 py-2 text-sm text-white">
          {t("habit.add")}
        </button>
      </form>

      {habits.length === 0 ? (
        <p className="text-sm text-gray-500">{t("habit.empty")}</p>
      ) : (
        <ul className="space-y-1">
          {habits.map((h) => (
            <li
              key={h.id}
              className="flex items-center gap-3 rounded border bg-white px-3 py-2"
            >
              {/* check button */}
              <button
                onClick={() => toggleLog.mutate(h.id)}
                className={`flex h-7 w-7 items-center justify-center rounded-full border-2 text-sm font-bold transition-colors ${
                  h.today_completed
                    ? "border-green-500 bg-green-500 text-white"
                    : "border-gray-300 text-gray-300 hover:border-green-400"
                }`}
              >
                {h.today_completed ? "✓" : ""}
              </button>

              <div className="flex-1">
                <span className={h.today_completed ? "text-gray-400 line-through" : ""}>
                  {h.name}
                </span>
                <span className="ms-2 text-xs text-gray-400">{scheduleLabel(h.schedule)}</span>
              </div>

              {h.streak > 0 && (
                <span className="text-xs font-medium text-orange-500">
                  🔥 {h.streak} {t("habit.streak")}
                </span>
              )}

              <button
                onClick={() => remove.mutate(h.id)}
                className="text-sm text-red-400 hover:text-red-600"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
