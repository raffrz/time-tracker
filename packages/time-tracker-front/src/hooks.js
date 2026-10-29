import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api.js";

// Relogio local que re-renderiza a cada `ms`.
export function useNow(ms = 1000) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return now;
}

// Estado do dia + relatorio + eventos do dia (linha do tempo). Recarrega a cada `refreshMs` e sob demanda (reload).
// `fetchedAt` permite somar o tempo decorrido desde a ultima leitura (tempo real).
export function useDay(refreshMs = 30000) {
  const [data, setData] = useState({ state: null, report: null, events: [], fetchedAt: Date.now() });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const alive = useRef(true);

  const reload = useCallback(async () => {
    try {
      const state = await api.state();
      let report = null;
      let events = [];
      if (state.status !== "not_started") {
        const [r, ev] = await Promise.all([
          api.report().catch((e) => {
            if (e instanceof ApiError && e.status === 409) return null;
            throw e;
          }),
          api.events(state.work_date, state.work_date),
        ]);
        report = r;
        events = ev;
      }
      if (alive.current) {
        setData({ state, report, events, fetchedAt: Date.now() });
        setError(null);
      }
    } catch (e) {
      if (alive.current) setError(e.message);
    } finally {
      if (alive.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    reload();
    const id = setInterval(reload, refreshMs);
    return () => {
      alive.current = false;
      clearInterval(id);
    };
  }, [reload, refreshMs]);

  return { ...data, error, loading, reload };
}

// Meta diaria em minutos, guardada no navegador (padrao 8h30).
const GOAL_KEY = "tt.dailyGoalMinutes";
export function useDailyGoal(defaultMinutes = 510) {
  const [minutes, setMinutes] = useState(() => {
    try {
      const v = parseInt(localStorage.getItem(GOAL_KEY), 10);
      return v > 0 ? v : defaultMinutes;
    } catch {
      return defaultMinutes;
    }
  });
  const save = useCallback((m) => {
    setMinutes(m);
    try {
      localStorage.setItem(GOAL_KEY, String(m));
    } catch {
      /* sem storage: vale so para esta sessao */
    }
  }, []);
  return [minutes, save];
}
