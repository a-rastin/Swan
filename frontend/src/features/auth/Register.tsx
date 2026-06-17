import type { FormEvent } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import api from "@/lib/api";

export default function Register() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/auth/register", { name, email, password, locale: i18n.language });
      navigate("/login");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-3 rounded-lg border bg-white p-6">
        <h1 className="text-xl font-semibold">{t("auth.register")} — {t("app.name")}</h1>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <input
          placeholder={t("auth.name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded border px-3 py-2"
        />
        <input
          type="email"
          placeholder={t("auth.email")}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border px-3 py-2"
          required
        />
        <input
          type="password"
          placeholder={t("auth.password")}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border px-3 py-2"
          minLength={8}
          required
        />
        <button className="w-full rounded bg-sky-600 py-2 text-white">{t("auth.register")}</button>
        <Link to="/login" className="block text-center text-sm text-sky-700">
          {t("auth.haveAccount")}
        </Link>
      </form>
    </div>
  );
}
