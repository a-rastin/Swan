import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";

interface FileItem {
  id: string;
  name: string;
  mime: string | null;
  size: number | null;
  web_view_link: string | null;
  created_at: string;
}

interface Props {
  attachedType: "task" | "project" | "list";
  attachedId: string;
}

function formatBytes(n: number | null): string {
  if (!n) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function FileAttachment({ attachedType, attachedId }: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === "fa";
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const queryKey = ["files", attachedType, attachedId];

  const { data: files = [] } = useQuery<FileItem[]>({
    queryKey,
    queryFn: async () =>
      (await api.get("/files", { params: { attached_type: attachedType, attached_id: attachedId } }))
        .data,
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post(
        `/files?attached_type=${attachedType}&attached_id=${attachedId}`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/files/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
  });

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500">
          {isFa ? "پیوست‌ها" : "Attachments"}
        </span>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="rounded border px-2 py-0.5 text-xs text-sky-600 hover:bg-sky-50"
        >
          {isFa ? "+ افزودن فایل" : "+ Add file"}
        </button>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) upload.mutate(f);
            e.target.value = "";
          }}
        />
      </div>

      {upload.isPending && (
        <p className="text-xs text-gray-400">{isFa ? "در حال آپلود..." : "Uploading..."}</p>
      )}

      {files.length > 0 && (
        <ul className="space-y-1">
          {files.map((f) => (
            <li key={f.id} className="flex items-center gap-2 rounded border bg-gray-50 px-2 py-1 text-xs">
              {f.web_view_link ? (
                <a
                  href={f.web_view_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 truncate text-sky-700 underline"
                >
                  {f.name}
                </a>
              ) : (
                <span className="flex-1 truncate">{f.name}</span>
              )}
              {f.size !== null && (
                <span className="text-gray-400">{formatBytes(f.size)}</span>
              )}
              <button
                type="button"
                onClick={() => remove.mutate(f.id)}
                className="text-red-400 hover:text-red-600"
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
