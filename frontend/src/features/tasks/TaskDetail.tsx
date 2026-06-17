import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";
import FileAttachment from "@/features/files/FileAttachment";
import RecurrencePicker from "./RecurrencePicker";

export interface Task {
  id: string;
  title: string;
  notes?: string | null;
  status: string;
  priority: number;
  due_at?: string | null;
  remind_at?: string | null;
  recurrence_rrule?: string | null;
  list_id?: string | null;
  project_id?: string | null;
  parent_task_id?: string | null;
  source: string;
  completed_at?: string | null;
}

interface Props {
  task: Task;
  onClose: () => void;
  invalidateKey: string[];
}

const PRIORITY_LABELS = ["None", "Low", "Medium", "High"];
const PRIORITY_LABELS_FA = ["بدون", "کم", "متوسط", "زیاد"];

function toDatetimeLocal(iso: string | null | undefined): string {
  if (!iso) return "";
  // slice to "YYYY-MM-DDTHH:MM"
  return iso.slice(0, 16);
}

function fromDatetimeLocal(val: string): string | null {
  if (!val) return null;
  return new Date(val).toISOString();
}

export default function TaskDetail({ task, onClose, invalidateKey }: Props) {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language === "fa";
  const qc = useQueryClient();

  const [title, setTitle] = useState(task.title);
  const [notes, setNotes] = useState(task.notes ?? "");
  const [priority, setPriority] = useState(task.priority);
  const [dueAt, setDueAt] = useState(toDatetimeLocal(task.due_at));
  const [remindAt, setRemindAt] = useState(toDatetimeLocal(task.remind_at));
  const [rrule, setRrule] = useState<string | null>(task.recurrence_rrule ?? null);

  useEffect(() => {
    setTitle(task.title);
    setNotes(task.notes ?? "");
    setPriority(task.priority);
    setDueAt(toDatetimeLocal(task.due_at));
    setRemindAt(toDatetimeLocal(task.remind_at));
    setRrule(task.recurrence_rrule ?? null);
  }, [task.id]);

  const save = useMutation({
    mutationFn: () =>
      api.patch(`/tasks/${task.id}`, {
        title,
        notes: notes || null,
        priority,
        due_at: fromDatetimeLocal(dueAt),
        remind_at: fromDatetimeLocal(remindAt),
        recurrence_rrule: rrule,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: invalidateKey });
      onClose();
    },
  });

  const del = useMutation({
    mutationFn: () => api.delete(`/tasks/${task.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: invalidateKey });
      onClose();
    },
  });

  const priorityLabels = isFa ? PRIORITY_LABELS_FA : PRIORITY_LABELS;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">{isFa ? "جزئیات کار" : "Task detail"}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700">✕</button>
        </div>

        <div className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t("task.title")}
            className="w-full rounded border px-3 py-2"
          />

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={isFa ? "یادداشت" : "Notes"}
            rows={3}
            className="w-full rounded border px-3 py-2 text-sm"
          />

          <div>
            <label className="mb-1 block text-xs text-gray-500">
              {isFa ? "اولویت" : "Priority"}
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full rounded border px-3 py-2 text-sm"
            >
              {priorityLabels.map((l, i) => (
                <option key={i} value={i}>{l}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">
              {isFa ? "موعد مقرر" : "Due date"}
            </label>
            <input
              type="datetime-local"
              value={dueAt}
              onChange={(e) => setDueAt(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">
              {isFa ? "یادآوری" : "Remind at"}
            </label>
            <input
              type="datetime-local"
              value={remindAt}
              onChange={(e) => setRemindAt(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">
              {isFa ? "تکرار" : "Recurrence"}
            </label>
            <RecurrencePicker value={rrule} onChange={setRrule} />
          </div>

          <div className="border-t pt-3">
            <FileAttachment attachedType="task" attachedId={task.id} />
          </div>
        </div>

        <div className="mt-4 flex justify-between">
          <button
            onClick={() => del.mutate()}
            className="rounded px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            {isFa ? "حذف" : "Delete"}
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="rounded border px-4 py-2 text-sm">
              {isFa ? "لغو" : "Cancel"}
            </button>
            <button
              onClick={() => save.mutate()}
              disabled={!title.trim() || save.isPending}
              className="rounded bg-sky-600 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              {isFa ? "ذخیره" : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
