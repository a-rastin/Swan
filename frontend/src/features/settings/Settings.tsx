import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";
import { useUser } from "@/lib/useUser";

// ─── sub-sections ────────────────────────────────────────────────────────────

function ProfileSection() {
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const { data: user } = useUser();
  const [name, setName] = useState(user?.name ?? "");
  const [locale, setLocale] = useState(user?.locale ?? "en");
  const [calPref, setCalPref] = useState(user?.calendar_pref ?? "gregorian");
  const [tz, setTz] = useState(user?.timezone ?? "UTC");
  const [ok, setOk] = useState(false);

  const save = useMutation({
    mutationFn: () =>
      api.patch("/users/me", { name, locale, calendar_pref: calPref, timezone: tz }),
    onSuccess: () => {
      i18n.changeLanguage(locale);
      qc.invalidateQueries({ queryKey: ["me"] });
      setOk(true);
      setTimeout(() => setOk(false), 2000);
    },
  });

  return (
    <div className="space-y-3">
      <h2 className="font-semibold">{t("nav.settings")}</h2>

      <label className="block text-sm">
        <span className="text-gray-600">{t("auth.name")}</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 w-full rounded border px-3 py-2"
        />
      </label>

      <label className="block text-sm">
        <span className="text-gray-600">{t("settings.language")}</span>
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          className="mt-1 w-full rounded border px-3 py-2"
        >
          <option value="en">English</option>
          <option value="fa">فارسی</option>
        </select>
      </label>

      <label className="block text-sm">
        <span className="text-gray-600">{t("settings.calendar")}</span>
        <select
          value={calPref}
          onChange={(e) => setCalPref(e.target.value)}
          className="mt-1 w-full rounded border px-3 py-2"
        >
          <option value="gregorian">{t("settings.gregorian")}</option>
          <option value="jalali">{t("settings.jalali")}</option>
        </select>
      </label>

      <label className="block text-sm">
        <span className="text-gray-600">Timezone</span>
        <input
          value={tz}
          onChange={(e) => setTz(e.target.value)}
          placeholder="Asia/Tehran"
          className="mt-1 w-full rounded border px-3 py-2"
        />
      </label>

      <button
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="rounded bg-sky-600 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {ok ? "✓ Saved" : "Save"}
      </button>
    </div>
  );
}


function PasswordSection() {
  const isFa = useTranslation().i18n.language === "fa";
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState(false);

  const save = useMutation({
    mutationFn: () =>
      api.patch("/users/me/password", { current_password: cur, new_password: next }),
    onSuccess: () => {
      setCur(""); setNext(""); setOk(true);
      setTimeout(() => setOk(false), 2000);
    },
    onError: () => setErr(isFa ? "رمز فعلی اشتباه است" : "Current password wrong"),
  });

  return (
    <div className="space-y-3 border-t pt-4">
      <h2 className="font-semibold">{isFa ? "تغییر رمز عبور" : "Change password"}</h2>
      {err && <p className="text-sm text-red-600">{err}</p>}
      <input
        type="password"
        placeholder={isFa ? "رمز فعلی" : "Current password"}
        value={cur}
        onChange={(e) => { setCur(e.target.value); setErr(""); }}
        className="w-full rounded border px-3 py-2 text-sm"
      />
      <input
        type="password"
        placeholder={isFa ? "رمز جدید (حداقل ۸ کاراکتر)" : "New password (min 8 chars)"}
        value={next}
        onChange={(e) => setNext(e.target.value)}
        minLength={8}
        className="w-full rounded border px-3 py-2 text-sm"
      />
      <button
        onClick={() => save.mutate()}
        disabled={!cur || next.length < 8 || save.isPending}
        className="rounded bg-sky-600 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {ok ? "✓" : (isFa ? "تغییر" : "Update")}
      </button>
    </div>
  );
}


interface ApiKey {
  id: string;
  name: string;
  scopes: string;
  last_used_at?: string | null;
}

function ApiKeysSection() {
  const isFa = useTranslation().i18n.language === "fa";
  const qc = useQueryClient();
  const [newName, setNewName] = useState("");
  const [rawKey, setRawKey] = useState<string | null>(null);

  const { data: keys = [] } = useQuery<ApiKey[]>({
    queryKey: ["apikeys"],
    queryFn: async () => (await api.get("/apikeys")).data,
  });

  const create = useMutation({
    mutationFn: async (name: string) => (await api.post("/apikeys", { name })).data,
    onSuccess: (data) => {
      setRawKey(data.raw_key);
      setNewName("");
      qc.invalidateQueries({ queryKey: ["apikeys"] });
    },
  });

  const revoke = useMutation({
    mutationFn: async (id: string) => api.delete(`/apikeys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["apikeys"] }),
  });

  return (
    <div className="space-y-3 border-t pt-4">
      <h2 className="font-semibold">{isFa ? "کلیدهای API" : "API Keys"}</h2>
      <p className="text-xs text-gray-500">
        {isFa
          ? "این کلیدها را در n8n استفاده کنید (هدر X-API-Key)."
          : "Use these keys in n8n (header X-API-Key)."}
      </p>

      {rawKey && (
        <div className="rounded border border-yellow-300 bg-yellow-50 p-3 text-sm">
          <p className="mb-1 font-medium text-yellow-800">
            {isFa ? "کلید فقط یک‌بار نشان داده می‌شود:" : "Key shown once — copy now:"}
          </p>
          <code className="break-all text-xs">{rawKey}</code>
          <button
            onClick={() => setRawKey(null)}
            className="mt-2 block text-xs text-yellow-700 underline"
          >
            {isFa ? "بستن" : "Dismiss"}
          </button>
        </div>
      )}

      <form
        onSubmit={(e) => { e.preventDefault(); if (newName.trim()) create.mutate(newName.trim()); }}
        className="flex gap-2"
      >
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder={isFa ? "نام کلید" : "Key name"}
          className="flex-1 rounded border px-3 py-2 text-sm"
        />
        <button className="rounded bg-sky-600 px-3 py-2 text-sm text-white">
          {isFa ? "ساخت" : "Create"}
        </button>
      </form>

      {keys.length > 0 && (
        <ul className="space-y-1">
          {keys.map((k) => (
            <li key={k.id} className="flex items-center justify-between rounded border bg-white px-3 py-2 text-sm">
              <div>
                <span className="font-medium">{k.name}</span>
                <span className="ms-2 text-xs text-gray-400">{k.scopes}</span>
                {k.last_used_at && (
                  <span className="ms-2 text-xs text-gray-400">
                    {isFa ? "آخرین استفاده:" : "Last used:"}{" "}
                    {new Date(k.last_used_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              <button
                onClick={() => revoke.mutate(k.id)}
                className="text-xs text-red-500 hover:text-red-700"
              >
                {isFa ? "لغو" : "Revoke"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


interface TgStatus {
  linked: boolean;
  telegram_chat_id: string | null;
  pending_code: string | null;
}

function TelegramSection() {
  const isFa = useTranslation().i18n.language === "fa";
  const qc = useQueryClient();

  const { data: tg } = useQuery<TgStatus>({
    queryKey: ["tg-status"],
    queryFn: async () => (await api.get("/telegram/status")).data,
  });

  const genCode = useMutation({
    mutationFn: async () => (await api.post("/telegram/code")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tg-status"] }),
  });

  const unlink = useMutation({
    mutationFn: async () => api.delete("/telegram/unlink"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tg-status"] }),
  });

  return (
    <div className="space-y-3 border-t pt-4">
      <h2 className="font-semibold">Telegram</h2>

      {tg?.linked ? (
        <div className="space-y-2">
          <p className="text-sm text-green-700">
            ✓ {isFa ? "متصل به" : "Linked to chat"} {tg.telegram_chat_id}
          </p>
          <button
            onClick={() => unlink.mutate()}
            className="text-sm text-red-500 hover:underline"
          >
            {isFa ? "قطع اتصال" : "Unlink"}
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-gray-500">
            {isFa
              ? "برای ربط دادن حساب تلگرام، کد زیر را به ربات n8n خود ارسال کنید:"
              : "To link Telegram, send this code to your n8n Telegram bot:"}
          </p>
          {tg?.pending_code ? (
            <div className="rounded border bg-gray-50 p-3">
              <p className="mb-1 text-xs text-gray-500">
                {isFa ? "ارسال به ربات:" : "Send to bot:"}
              </p>
              <code className="text-lg font-bold tracking-widest">/link {tg.pending_code}</code>
              <button
                onClick={() => genCode.mutate()}
                className="ms-4 text-xs text-sky-600 underline"
              >
                {isFa ? "تازه‌سازی" : "Refresh"}
              </button>
            </div>
          ) : (
            <button
              onClick={() => genCode.mutate()}
              className="rounded bg-sky-600 px-4 py-2 text-sm text-white"
            >
              {isFa ? "دریافت کد" : "Get link code"}
            </button>
          )}
        </div>
      )}

      <div className="rounded border bg-blue-50 p-3 text-xs text-blue-700 space-y-1">
        <p className="font-semibold">{isFa ? "راهنمای n8n:" : "n8n setup:"}</p>
        <p>{isFa ? "۱. ربات تلگرام در n8n راه‌اندازی کنید." : "1. Set up a Telegram bot trigger in n8n."}</p>
        <p>{isFa ? "۲. یک HTTP Request اضافه کنید:" : "2. Add an HTTP Request node:"}</p>
        <code className="block bg-blue-100 px-2 py-1 rounded mt-1">
          POST https://{'<domain>'}/api/external/telegram/link<br />
          X-API-Key: {'<EXTERNAL_API_MASTER_KEY>'}<br />
          {`{"chat_id": "{{$json.chat.id}}", "link_code": "{{$json.text.split(' ')[1]}}"}`}
        </code>
        <p>{isFa ? "۳. کد `/link XXXXXXXX` را به ربات بفرستید." : "3. Send /link XXXXXXXX to the bot."}</p>
      </div>
    </div>
  );
}


// ─── main Settings page ───────────────────────────────────────────────────────

export default function Settings() {
  return (
    <div className="max-w-md space-y-0">
      <ProfileSection />
      <PasswordSection />
      <ApiKeysSection />
      <TelegramSection />
    </div>
  );
}
