import { useState } from "react";
import { api } from "../api.js";
import { useDailyGoal, useDay, useNow } from "../hooks.js";
import {
  formatClock,
  formatDecimalHours,
  formatDuration,
  formatHoursMinutes,
  greeting,
  parseTimeSpent,
} from "../format.js";
import Commands, { StartDayForm } from "../components/Commands.jsx";
import Timeline from "../components/Timeline.jsx";
import Modal from "../components/Modal.jsx";
import {
  IconChevronRight,
  IconClock,
  IconCoffee,
  IconList,
  IconPause,
  IconPlay,
  IconTarget,
  IconTerminal,
} from "../components/Icons.jsx";

const USER_NAME = import.meta.env.VITE_USER_NAME || "";

const STATUS = {
  not_started: { label: "Dia não iniciado", tone: "idle" },
  in_progress: { label: "Em andamento", tone: "ok" },
  paused: { label: "Pausado", tone: "warn" },
  ended: { label: "Dia finalizado", tone: "idle" },
};

const pct = (part, whole) => (whole > 0 ? Math.round((part / whole) * 100) : 0);
const clamp01 = (x) => Math.min(1, Math.max(0, x));
const pad = (n) => String(n).padStart(2, "0");

// Anel de progresso da meta com o botao de pausar/retomar no centro.
function Ring({ progress, status, busy, onToggle }) {
  const r = 58;
  const c = 2 * Math.PI * r;
  const running = status === "in_progress";
  const canToggle = running || status === "paused";
  return (
    <div className={`ring ${status}`}>
      <svg viewBox="0 0 140 140" width="140" height="140" aria-hidden>
        <circle className="ring-track" cx="70" cy="70" r={r} />
        <circle
          className="ring-fill"
          cx="70"
          cy="70"
          r={r}
          strokeDasharray={c}
          strokeDashoffset={c * (1 - clamp01(progress))}
          transform="rotate(-90 70 70)"
        />
      </svg>
      {canToggle && (
        <button
          className="ring-btn"
          onClick={onToggle}
          disabled={busy}
          title={running ? "Pausar agora" : "Retomar agora"}
          aria-label={running ? "Pausar agora" : "Retomar agora"}
        >
          {running ? <IconPause size={24} /> : <IconPlay size={24} />}
        </button>
      )}
    </div>
  );
}

function Bar({ value, tone }) {
  return (
    <div className="bar">
      <div className={`bar-fill ${tone || ""}`} style={{ width: `${clamp01(value) * 100}%` }} />
    </div>
  );
}

function GoalModal({ minutes, onSave, onClose }) {
  const [value, setValue] = useState(formatHoursMinutes(minutes * 60));
  const [error, setError] = useState(null);
  function submit(e) {
    e.preventDefault();
    const m = parseTimeSpent(value);
    if (!(m > 0) || m > 24 * 60) return setError("Use 8:00, 8h, 7h30 ou 480.");
    onSave(m);
    onClose();
  }
  return (
    <Modal title="Meta diária" onClose={onClose}>
      <form className="action-form" onSubmit={submit}>
        <label className="field">
          <span>Horas por dia</span>
          <input value={value} onChange={(e) => setValue(e.target.value)} autoFocus />
        </label>
        {error && <div className="banner error">{error}</div>}
        <div className="form-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn ok">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}

export default function TodayPage() {
  const { state, report, events, fetchedAt, error, loading, reload } = useDay();
  const now = useNow(1000);
  const [goalMinutes, setGoalMinutes] = useDailyGoal();
  const [editGoal, setEditGoal] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [actionError, setActionError] = useState(null);

  if (loading) return <p className="muted">Carregando…</p>;
  if (!state) return <div className="banner error">{error}</div>;

  // Tempo real: soma o decorrido desde a ultima leitura enquanto o cronometro corre.
  const elapsed = Math.max(0, (now - fetchedAt) / 1000);
  const status = state.status;
  const running = status === "in_progress";
  const worked = (report?.total_seconds ?? 0) + (running ? elapsed : 0);
  const paused = (report?.paused_seconds ?? 0) + (status === "paused" ? elapsed : 0);
  const goal = goalMinutes * 60;
  const remaining = Math.max(0, goal - worked);
  const st = STATUS[status];

  // Pausa atual: desde o ultimo PAUSE.
  const lastPause = status === "paused"
    ? events.filter((e) => e.event_type === "PAUSE").sort((a, b) => b.occurred_at.localeCompare(a.occurred_at))[0]
    : null;
  const pausedFor = lastPause ? (now - new Date(lastPause.occurred_at)) / 1000 : 0;

  // Saida prevista: agora + restante (so faz sentido com o relogio correndo).
  const eta = running && remaining > 0 ? new Date(now + remaining * 1000) : null;

  // Tarefas com o tempo da principal atual correndo ao vivo.
  const tasks = (report?.tasks ?? []).map((t) =>
    running && t.kind === "main" && t.task_id === state.current_task ? { ...t, seconds: t.seconds + elapsed } : t
  );
  const currentTaskSeconds =
    tasks.find((t) => t.kind === "main" && t.task_id === state.current_task)?.seconds ?? 0;

  const subtitle = {
    not_started: "Informe a tarefa principal para começar a contar.",
    in_progress: `Continue assim. Você já trabalhou ${formatDuration(worked)} hoje.`,
    paused: `Em pausa${lastPause ? ` há ${formatDuration(pausedFor)}` : ""}. Você já trabalhou ${formatDuration(worked)} hoje.`,
    ended: `Dia finalizado com ${formatDuration(worked)} trabalhadas.`,
  }[status];

  async function done() {
    setActionError(null);
    await reload();
  }

  async function toggle() {
    setToggling(true);
    try {
      if (running) await api.pause(null, null);
      else await api.resume(null);
      await done();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setToggling(false);
    }
  }

  return (
    <div className="today">
      <div className="today-main">
        <header className="hello">
          <div>
            <h1>
              {greeting(new Date(now))}
              {USER_NAME ? `, ${USER_NAME}` : ""}!
            </h1>
            <p className="hello-sub">{subtitle}</p>
          </div>
          <span className={`badge ${st.tone}`}>
            <span className="badge-dot" />
            {st.label}
          </span>
        </header>

        {(error || actionError) && <div className="banner error">{actionError || error}</div>}

        {/* ---- cronometro principal ---- */}
        <section className={`hero ${status}`}>
          <div className="hero-clock">
            <Ring progress={worked / goal} status={status} busy={toggling} onToggle={toggle} />
            <div>
              <div className="big-clock">{formatClock(worked)}</div>
              <div className="hero-label">Horas trabalhadas</div>
              <div className="hero-hint">
                <IconClock size={16} /> {formatDecimalHours(worked)} h
              </div>
            </div>
          </div>

          {status === "not_started" ? (
            <div className="hero-start">
              <StartDayForm onDone={done} />
            </div>
          ) : (
            <div className="hero-stats">
              <div className={`mini-stat ${status === "paused" ? "live-pause" : ""}`}>
                <IconCoffee size={20} className="mini-icon pause" />
                <div className="mini-label">Pausa</div>
                <div className="mini-value">{formatClock(paused)}</div>
                <div className="mini-hint">
                  {formatDecimalHours(paused)} h{lastPause ? ` · atual ${formatDuration(pausedFor)}` : ""}
                </div>
              </div>
              <div className="mini-stat">
                <IconTarget size={20} className="mini-icon ok" />
                <div className="mini-label">Meta do dia</div>
                <div className="mini-value">{formatHoursMinutes(goal)} h</div>
                <Bar value={worked / goal} tone="ok" />
                <div className="mini-hint">{pct(worked, goal)}%</div>
              </div>
            </div>
          )}
        </section>

        <Commands status={status} currentTask={state.current_task} onDone={done} />

        {/* ---- tarefa atual ---- */}
        {state.current_task && status !== "ended" && (
          <section className="current-task">
            <span className="task-icon">
              <IconTerminal size={22} />
            </span>
            <div className="ct-info">
              <div className="ct-label">Tarefa atual</div>
              <div className="ct-row">
                <span className="ct-id">{state.current_task}</span>
                <span className="tag main">Tarefa principal</span>
              </div>
            </div>
            <div className="ct-time">
              <div className="ct-label">Tempo na tarefa</div>
              <div className="ct-clock">{formatClock(currentTaskSeconds)}</div>
              <div className="muted small">({formatDecimalHours(currentTaskSeconds)} h)</div>
            </div>
          </section>
        )}

        {/* ---- tarefas do dia ---- */}
        {tasks.length > 0 && (
          <section className="panel">
            <h2 className="panel-title">
              <IconList size={22} /> Tarefas do dia
            </h2>
            <table className="table tasks-table">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Tarefa</th>
                  <th className="num">Tempo</th>
                  <th className="num">%</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={`${t.kind}-${t.task_id}`}>
                    <td>
                      <span className={`tag ${t.kind}`}>{t.kind === "main" ? "principal" : "side-task"}</span>
                    </td>
                    <td className="task-cell">
                      <div className="task-name">{t.task_id}</div>
                      <Bar value={worked > 0 ? t.seconds / worked : 0} tone={t.kind === "main" ? "ok" : "side"} />
                    </td>
                    <td className="num strong">{formatDecimalHours(t.seconds)} h</td>
                    <td className="num muted">{pct(t.seconds, worked)}%</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={2}>Total</td>
                  <td className="num">{formatDecimalHours(worked)} h</td>
                  <td className="num muted">100%</td>
                </tr>
              </tfoot>
            </table>
          </section>
        )}
      </div>

      {/* ---- coluna lateral ---- */}
      <aside className="today-side">
        <section className="panel">
          <h2 className="panel-title">
            <IconClock size={22} /> Visual do dia
          </h2>
          <div className="legend-row">
            <span className="dot ok" /> Trabalho
            <span className="legend-val">{formatDecimalHours(worked)} h</span>
            <span className="legend-pct">{pct(worked, goal)}%</span>
          </div>
          <Bar value={worked / goal} tone="ok" />
          <div className="legend-row">
            <span className="dot pause" /> Pausas
            <span className="legend-val">{formatDecimalHours(paused)} h</span>
            <span className="legend-pct">{pct(paused, goal)}%</span>
          </div>
          <Bar value={paused / goal} tone="pause" />
          <div className="legend-row">
            <span className="dot idle" /> Restante
            <span className="legend-val">{formatDecimalHours(remaining)} h</span>
            <span className="legend-pct">{pct(remaining, goal)}%</span>
          </div>
          <Bar value={remaining / goal} tone="idle" />
          <p className="muted small legend-note">Percentuais em relação à meta diária.</p>

          <button className="goal-card" onClick={() => setEditGoal(true)}>
            <span className="goal-icon">
              <IconTarget size={22} />
            </span>
            <span className="goal-text">
              <span className="muted">Meta diária</span>
              <strong>{formatHoursMinutes(goal)} h</strong>
              {eta && (
                <span className="small muted">
                  Saída prevista ~{pad(eta.getHours())}:{pad(eta.getMinutes())}
                </span>
              )}
              {worked >= goal && <span className="small ok-text">Meta atingida!</span>}
            </span>
            <IconChevronRight size={18} />
          </button>
        </section>

        {status !== "not_started" && <Timeline events={events} now={now} />}
      </aside>

      {editGoal && <GoalModal minutes={goalMinutes} onSave={setGoalMinutes} onClose={() => setEditGoal(false)} />}
    </div>
  );
}
