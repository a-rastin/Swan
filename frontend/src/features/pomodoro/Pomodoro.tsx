import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import api from "@/lib/api";

type Phase = "work" | "short_break" | "long_break";

interface Settings {
  work_min: number;
  short_break: number;
  long_break: number;
  cycles_before_long: number;
  auto_start: boolean;
}

interface Stats {
  today_work_minutes: number;
  week_work_minutes: number;
  today_sessions: number;
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function fmt(seconds: number) {
  return `${pad(Math.floor(seconds / 60))}:${pad(seconds % 60)}`;
}

function phaseDuration(phase: Phase, settings: Settings): number {
  if (phase === "work") return settings.work_min * 60;
  if (phase === "short_break") return settings.short_break * 60;
  return settings.long_break * 60;
}

export default function Pomodoro() {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const { data: settings } = useQuery<Settings>({
    queryKey: ["pomodoro-settings"],
    queryFn: async () => (await api.get("/pomodoro/settings")).data,
  });

  const { data: stats } = useQuery<Stats>({
    queryKey: ["pomodoro-stats"],
    queryFn: async () => (await api.get("/pomodoro/stats")).data,
  });

  const [phase, setPhase] = useState<Phase>("work");
  const [remaining, setRemaining] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [cycleCount, setCycleCount] = useState(0);
  const [showSettings, setShowSettings] = useState(false);

  const endTimeRef = useRef<number | null>(null);
  const sessionStartRef = useRef<Date | null>(null);

  // Initialise / reset remaining when settings load or phase changes
  useEffect(() => {
    if (settings && !running) {
      setRemaining(phaseDuration(phase, settings));
    }
  }, [settings, phase]);

  // Tick
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      if (endTimeRef.current === null) return;
      const left = Math.ceil((endTimeRef.current - Date.now()) / 1000);
      if (left <= 0) {
        clearInterval(id);
        setRunning(false);
        handlePhaseEnd();
      } else {
        setRemaining(left);
      }
    }, 250);
    return () => clearInterval(id);
  }, [running]);

  const logSession = useMutation({
    mutationFn: (body: object) => api.post("/pomodoro/sessions", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pomodoro-stats"] }),
  });

  function handlePhaseEnd() {
    if (phase === "work" && sessionStartRef.current && settings) {
      logSession.mutate({
        type: "work",
        started_at: sessionStartRef.current.toISOString(),
        ended_at: new Date().toISOString(),
        completed: true,
      });
      const newCycle = cycleCount + 1;
      setCycleCount(newCycle);
      const nextPhase: Phase =
        newCycle % settings.cycles_before_long === 0 ? "long_break" : "short_break";
      setPhase(nextPhase);
      if (settings.auto_start) startPhase(nextPhase);
      else setRemaining(phaseDuration(nextPhase, settings));
    } else if (settings) {
      setPhase("work");
      if (settings.auto_start) startPhase("work");
      else setRemaining(phaseDuration("work", settings));
    }
  }

  function startPhase(p: Phase = phase) {
    if (!settings) return;
    const dur = phaseDuration(p, settings) * 1000;
    endTimeRef.current = Date.now() + dur;
    sessionStartRef.current = new Date();
    setRunning(true);
  }

  function pause() {
    setRunning(false);
    // endTimeRef stays so resume works
  }

  function resume() {
    if (remaining === null || !settings) return;
    endTimeRef.current = Date.now() + remaining * 1000;
    setRunning(true);
  }

  function reset() {
    setRunning(false);
    endTimeRef.current = null;
    sessionStartRef.current = null;
    if (settings) setRemaining(phaseDuration(phase, settings));
  }

  const phaseLabel = {
    work: t("pomodoro.work"),
    short_break: t("pomodoro.shortBreak"),
    long_break: t("pomodoro.longBreak"),
  }[phase];

  const phaseColor = {
    work: "text-sky-600",
    short_break: "text-green-600",
    long_break: "text-purple-600",
  }[phase];

  if (!settings) return <div className="text-sm text-gray-400">Loading…</div>;

  return (
    <div className="max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.pomodoro")}</h1>

      {/* timer */}
      <div className="mb-6 rounded-lg border bg-white p-8 text-center">
        <div className={`mb-1 text-sm font-medium ${phaseColor}`}>{phaseLabel}</div>
        <div className="mb-1 font-mono text-6xl font-bold">
          {fmt(remaining ?? phaseDuration(phase, settings))}
        </div>
        <div className="mb-4 text-xs text-gray-400">
          {t("pomodoro.cycle")} {cycleCount + 1}
        </div>

        <div className="flex justify-center gap-2">
          {!running ? (
            <button
              onClick={() => (endTimeRef.current ? resume() : startPhase())}
              className="rounded bg-sky-600 px-5 py-2 text-white"
            >
              {t("pomodoro.start")}
            </button>
          ) : (
            <button
              onClick={pause}
              className="rounded bg-yellow-500 px-5 py-2 text-white"
            >
              {t("pomodoro.pause")}
            </button>
          )}
          <button onClick={reset} className="rounded border px-5 py-2">
            {t("pomodoro.reset")}
          </button>
        </div>

        {/* phase selector */}
        <div className="mt-4 flex justify-center gap-2">
          {(["work", "short_break", "long_break"] as Phase[]).map((p) => (
            <button
              key={p}
              onClick={() => {
                if (running) return;
                setPhase(p);
                setRemaining(phaseDuration(p, settings));
                endTimeRef.current = null;
              }}
              className={`rounded px-2 py-1 text-xs ${
                phase === p ? "bg-gray-200 font-semibold" : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {{ work: t("pomodoro.work"), short_break: t("pomodoro.shortBreak"), long_break: t("pomodoro.longBreak") }[p]}
            </button>
          ))}
        </div>
      </div>

      {/* stats */}
      {stats && (
        <div className="mb-4 flex gap-3 text-center text-sm">
          <div className="flex-1 rounded border bg-white p-3">
            <div className="text-lg font-bold">{stats.today_work_minutes}</div>
            <div className="text-xs text-gray-500">{t("pomodoro.todayFocus")} ({t("pomodoro.minutes")})</div>
          </div>
          <div className="flex-1 rounded border bg-white p-3">
            <div className="text-lg font-bold">{stats.today_sessions}</div>
            <div className="text-xs text-gray-500">{t("pomodoro.work")}</div>
          </div>
        </div>
      )}

      {/* settings toggle */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        {t("pomodoro.settings")} {showSettings ? "▲" : "▼"}
      </button>

      {showSettings && <PomodoroSettingsPanel settings={settings} onSaved={() => {
        qc.invalidateQueries({ queryKey: ["pomodoro-settings"] });
        reset();
      }} />}
    </div>
  );
}


function PomodoroSettingsPanel({ settings, onSaved }: { settings: Settings; onSaved: () => void }) {
  const { t } = useTranslation();
  const [work, setWork] = useState(settings.work_min);
  const [short_, setShort] = useState(settings.short_break);
  const [long_, setLong] = useState(settings.long_break);
  const [cycles, setCycles] = useState(settings.cycles_before_long);

  const save = useMutation({
    mutationFn: () =>
      api.patch("/pomodoro/settings", {
        work_min: work,
        short_break: short_,
        long_break: long_,
        cycles_before_long: cycles,
      }),
    onSuccess: onSaved,
  });

  return (
    <div className="mt-3 space-y-2 rounded border bg-white p-4 text-sm">
      {[
        { label: t("pomodoro.workMin"),  val: work,   set: setWork },
        { label: t("pomodoro.shortMin"), val: short_,  set: setShort },
        { label: t("pomodoro.longMin"),  val: long_,   set: setLong },
        { label: t("pomodoro.cycles"),   val: cycles, set: setCycles },
      ].map(({ label, val, set }) => (
        <div key={label} className="flex items-center justify-between gap-4">
          <span className="text-gray-600">{label}</span>
          <input
            type="number"
            min={1}
            max={120}
            value={val}
            onChange={(e) => set(Number(e.target.value))}
            className="w-16 rounded border px-2 py-1 text-center"
          />
        </div>
      ))}
      <button
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="mt-1 w-full rounded bg-sky-600 py-1.5 text-white disabled:opacity-50"
      >
        Save
      </button>
    </div>
  );
}
