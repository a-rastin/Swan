import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";
import { useVoiceRecorder } from "./useVoiceRecorder";

interface CreatedTask {
  id: string;
  title: string;
  priority: number;
  due_at?: string | null;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string | null;
  resulting_task_ids?: string[] | null;
  created_at: string;
  // client-only: tasks embedded after auto-create
  _created_tasks?: CreatedTask[];
}

interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  messages: Message[];
}

export default function AiChat() {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language === "fa";
  const qc = useQueryClient();

  const [convId, setConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const voice = useVoiceRecorder();

  // Load saved conversation if any
  const { data: conversations = [] } = useQuery<Conversation[]>({
    queryKey: ["ai-conversations"],
    queryFn: async () => (await api.get("/ai/conversations")).data,
  });

  // Load messages when convId set
  useEffect(() => {
    if (!convId) return;
    api.get(`/ai/conversations/${convId}`).then((r) => {
      setMessages(r.data.messages ?? []);
    });
  }, [convId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendText = useMutation({
    mutationFn: async (msg: string) =>
      (await api.post("/ai/chat", { text: msg, conversation_id: convId })).data,
    onSuccess: (data) => {
      setConvId(data.conversation_id);
      qc.invalidateQueries({ queryKey: ["ai-conversations"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
      setMessages((prev) => [
        ...prev,
        {
          id: data.message_id + "-u",
          role: "user",
          content: text,
          created_at: new Date().toISOString(),
        },
        {
          id: data.message_id,
          role: "assistant",
          content: data.reply,
          _created_tasks: data.created_tasks,
          created_at: new Date().toISOString(),
        },
      ]);
      setText("");
    },
  });

  const sendVoice = useMutation({
    mutationFn: async (blob: Blob) => {
      const fd = new FormData();
      fd.append("audio", blob, `voice.${blob.type.split("/")[1] || "webm"}`);
      if (convId) fd.append("conversation_id", convId);
      return (await api.post("/ai/voice", fd, { headers: { "Content-Type": "multipart/form-data" } })).data;
    },
    onSuccess: (data) => {
      setConvId(data.conversation_id);
      qc.invalidateQueries({ queryKey: ["ai-conversations"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
      setMessages((prev) => [
        ...prev,
        {
          id: data.message_id + "-u",
          role: "user",
          content: isFa ? "🎤 پیام صوتی" : "🎤 Voice message",
          created_at: new Date().toISOString(),
        },
        {
          id: data.message_id,
          role: "assistant",
          content: data.reply,
          _created_tasks: data.created_tasks,
          created_at: new Date().toISOString(),
        },
      ]);
      voice.clear();
    },
  });

  const newConversation = async () => {
    const { data } = await api.post("/ai/conversations");
    setConvId(data.id);
    setMessages([]);
    qc.invalidateQueries({ queryKey: ["ai-conversations"] });
  };

  const handleMic = () => {
    if (voice.recording) {
      voice.stop();
    } else {
      voice.start().catch(() => alert(isFa ? "دسترسی به میکروفن رد شد" : "Microphone access denied"));
    }
  };

  // Auto-send voice blob when recording stops
  useEffect(() => {
    if (voice.blob) sendVoice.mutate(voice.blob);
  }, [voice.blob]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) sendText.mutate(text.trim());
  };

  const pending = sendText.isPending || sendVoice.isPending;

  return (
    <div className="flex h-[calc(100vh-7rem)] max-w-2xl flex-col">
      {/* header */}
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-xl font-semibold">{t("nav.ai")}</h1>
        <div className="flex gap-2">
          {/* conversation history picker */}
          {conversations.length > 0 && (
            <select
              value={convId ?? ""}
              onChange={(e) => setConvId(e.target.value || null)}
              className="rounded border px-2 py-1 text-sm"
            >
              <option value="">{isFa ? "مکالمه فعلی" : "Current"}</option>
              {conversations.map((c) => (
                <option key={c.id} value={c.id}>
                  {new Date(c.created_at).toLocaleDateString(i18n.language === "fa" ? "fa-IR" : "en-US")}
                </option>
              ))}
            </select>
          )}
          <button
            onClick={newConversation}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-100"
          >
            {isFa ? "+ جدید" : "+ New"}
          </button>
        </div>
      </div>

      {/* messages */}
      <div className="flex-1 overflow-y-auto rounded border bg-white p-3 space-y-3">
        {messages.length === 0 && (
          <p className="text-center text-sm text-gray-400 mt-8">
            {isFa
              ? "از دستیار بپرسید یا وظیفه‌ای بگویید تا اضافه کند."
              : "Ask the assistant anything, or describe tasks to add."}
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-sky-600 text-white"
                  : "border bg-gray-50 text-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m._created_tasks && m._created_tasks.length > 0 && (
                <div className="mt-2 space-y-1 border-t pt-2">
                  <p className="text-xs font-medium text-gray-500">
                    {isFa ? "✅ کارهای اضافه‌شده:" : "✅ Tasks added:"}
                  </p>
                  {m._created_tasks.map((task) => (
                    <div key={task.id} className="rounded bg-white px-2 py-1 text-xs text-gray-700 border">
                      {task.title}
                      {task.due_at && (
                        <span className="ms-2 text-gray-400">
                          {new Date(task.due_at).toLocaleDateString(
                            i18n.language === "fa" ? "fa-IR-u-ca-persian" : "en-US"
                          )}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {pending && (
          <div className="flex justify-start">
            <div className="rounded-lg border bg-gray-50 px-3 py-2 text-sm text-gray-400">
              {isFa ? "در حال پردازش…" : "Thinking…"}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* input bar */}
      <form onSubmit={submit} className="mt-2 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={isFa ? "پیام بنویسید…" : "Type a message…"}
          disabled={pending || voice.recording}
          className="flex-1 rounded border px-3 py-2 text-sm disabled:opacity-50"
        />
        {/* mic button */}
        <button
          type="button"
          onClick={handleMic}
          disabled={pending}
          className={`rounded px-3 py-2 text-sm ${
            voice.recording
              ? "animate-pulse bg-red-500 text-white"
              : "border hover:bg-gray-100"
          }`}
          title={voice.recording ? (isFa ? "توقف ضبط" : "Stop recording") : (isFa ? "ضبط صدا" : "Record voice")}
        >
          {voice.recording ? "⏹" : "🎤"}
        </button>
        <button
          type="submit"
          disabled={!text.trim() || pending}
          className="rounded bg-sky-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {isFa ? "ارسال" : "Send"}
        </button>
      </form>
    </div>
  );
}
