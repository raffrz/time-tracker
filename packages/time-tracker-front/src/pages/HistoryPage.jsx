import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { formatDate, formatTime } from "../format.js";
import DayHours from "../components/DayHours.jsx";

const TYPE_LABEL = {
  START_DAY: "Início do dia",
  PAUSE: "Pausa",
  RESUME: "Retomada",
  CHANGE_TASK: "Troca de tarefa",
  SIDE_TASK: "Side-task",
  END_DAY: "Fim do dia",
};

function details(e) {
  const parts = [];
  if (e.event_type === "SIDE_TASK") {
    parts.push(`${e.minutes} min`);
    if (e.description) parts.push(e.description);
  }
  if (e.event_type === "PAUSE" && e.auto_resume_at) {
    parts.push(`retomada prevista ${formatTime(e.auto_resume_at)}`);
  }
  return parts.join(" · ");
}

export default function HistoryPage() {
  const [events, setEvents] = useState([]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const [openHours, setOpenHours] = useState(() => new Set());
  const [version, setVersion] = useState(0);

  const load = useCallback(async () => {
    try {
      setEvents(await api.events(start, end));
      setVersion((v) => v + 1);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [start, end]);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(e) {
    const what = `${TYPE_LABEL[e.event_type]} das ${formatTime(e.occurred_at)} (${formatDate(e.work_date)})`;
    if (!window.confirm(`Excluir o registro "${what}"?\nO tempo do dia será recalculado.`)) return;
    setDeleting(e.id);
    try {
      await api.deleteEvent(e.id);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  }

  function toggleHours(day) {
    setOpenHours((prev) => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  }

  // API devolve do mais recente ao mais antigo; agrupa por dia mantendo a ordem.
  const days = useMemo(() => {
    const map = new Map();
    for (const e of events) {
      if (!map.has(e.work_date)) map.set(e.work_date, []);
      map.get(e.work_date).push(e);
    }
    return [...map.entries()];
  }, [events]);

  return (
    <>
      <header className="page-header">
        <h1>Histórico</h1>
        <span className="muted">{events.length} registros</span>
      </header>

      <section className="card filters">
        <label className="field">
          <span>De</span>
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        </label>
        <label className="field">
          <span>Até</span>
          <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </label>
        {(start || end) && (
          <button
            className="btn ghost"
            onClick={() => {
              setStart("");
              setEnd("");
            }}
          >
            Limpar filtro
          </button>
        )}
      </section>

      {error && <div className="banner error">{error}</div>}
      {loading && <p className="muted">Carregando…</p>}
      {!loading && !error && days.length === 0 && <p className="muted">Nenhum registro.</p>}

      {days.map(([day, list]) => (
        <section className="card" key={day}>
          <div className="day-header">
            <h2>{formatDate(day)}</h2>
            <button className="btn ghost" onClick={() => toggleHours(day)}>
              {openHours.has(day) ? "Ocultar horas" : "Horas por tarefa"}
            </button>
          </div>
          {openHours.has(day) && <DayHours day={day} version={version} />}
          <table className="table">
            <thead>
              <tr>
                <th>Hora</th>
                <th>Evento</th>
                <th>Tarefa</th>
                <th>Detalhes</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {list.map((e) => (
                <tr key={e.id}>
                  <td className="mono">{formatTime(e.occurred_at)}</td>
                  <td>
                    <span className={`tag ev-${e.event_type}`}>{TYPE_LABEL[e.event_type]}</span>
                  </td>
                  <td>{e.task_id ?? "—"}</td>
                  <td className="muted">{details(e) || "—"}</td>
                  <td className="num">
                    <button
                      className="btn danger small-btn"
                      disabled={deleting === e.id}
                      onClick={() => remove(e)}
                      title="Excluir registro"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </>
  );
}
