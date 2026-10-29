import { useState } from "react";
import { api } from "../api.js";
import { parseTimeSpent, todayAt } from "../format.js";
import Modal from "./Modal.jsx";
import { IconPause, IconPlay, IconPlus, IconStop, IconSwap } from "./Icons.jsx";

const Field = ({ label, children }) => (
  <label className="field">
    <span>{label}</span>
    {children}
  </label>
);

// Formulario generico: executa `run(valores)`, mostra o erro no proprio formulario e avisa o pai.
function ActionForm({ submit, tone, initial, run, onDone, onCancel, children }) {
  const [values, setValues] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.value }));

  async function handle(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await run(values);
      setValues(initial);
      await onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="action-form" onSubmit={handle}>
      <div className="fields">{children(values, set)}</div>
      {error && <div className="banner error">{error}</div>}
      <div className="form-actions">
        {onCancel && (
          <button type="button" className="btn ghost" onClick={onCancel}>
            Cancelar
          </button>
        )}
        <button className={`btn ${tone || "primary"}`} disabled={busy}>
          {busy ? "…" : submit}
        </button>
      </div>
    </form>
  );
}

// Formulario de inicio do dia (exibido no lugar do cronometro quando o dia nao comecou).
export function StartDayForm({ onDone }) {
  return (
    <ActionForm
      submit="Iniciar o dia"
      tone="ok"
      initial={{ task: "", at: "" }}
      run={(v) => api.startDay(v.task.trim(), todayAt(v.at))}
      onDone={onDone}
    >
      {(v, set) => (
        <div className="row-fields">
          <Field label="Tarefa principal">
            <input value={v.task} onChange={set("task")} placeholder="TASK-123" required autoFocus />
          </Field>
          <Field label="Início (opcional)">
            <input type="time" value={v.at} onChange={set("at")} />
          </Field>
        </div>
      )}
    </ActionForm>
  );
}

// Definicao das acoes: tile (icone, titulo, dica) + formulario do modal.
function actionsFor(status, currentTask) {
  const pauseOrResume =
    status === "paused"
      ? {
          id: "resume",
          tone: "ok",
          icon: IconPlay,
          title: "Retomar",
          hint: "(opcional horário)",
          modalHint: "Deixe em branco para retomar agora, ou informe quando você voltou.",
          submit: "Retomar",
          initial: { at: "" },
          run: (v) => api.resume(todayAt(v.at)),
          fields: (v, set) => (
            <Field label="Voltei às (opcional)">
              <input type="time" value={v.at} onChange={set("at")} />
            </Field>
          ),
        }
      : {
          id: "pause",
          tone: "warn",
          icon: IconPause,
          title: "Pausar",
          hint: "(opcional horário)",
          modalHint: "Deixe em branco para pausar agora. Retroativo: informe quando a pausa começou.",
          submit: "Pausar",
          initial: { since: "", back: "" },
          run: (v) => api.pause(todayAt(v.back), todayAt(v.since)),
          fields: (v, set) => (
            <div className="row-fields">
              <Field label="Pausa começou às (opcional)">
                <input type="time" value={v.since} onChange={set("since")} />
              </Field>
              <Field label="Retomada prevista (opcional)">
                <input type="time" value={v.back} onChange={set("back")} />
              </Field>
            </div>
          ),
        };

  return [
    pauseOrResume,
    {
      id: "change",
      tone: "primary",
      icon: IconSwap,
      title: "Trocar tarefa",
      hint: "(nova principal)",
      modalHint: `Tarefa atual: ${currentTask ?? "—"}. As horas da anterior são mantidas.`,
      submit: "Trocar",
      initial: { task: "" },
      run: (v) => api.changeTask(v.task.trim()),
      fields: (v, set) => (
        <Field label="Nova tarefa">
          <input value={v.task} onChange={set("task")} placeholder="TASK-456" required autoFocus />
        </Field>
      ),
    },
    {
      id: "side",
      tone: "side",
      icon: IconPlus,
      title: "Lançar side-task",
      hint: "(tempo e descrição)",
      modalHint: "O tempo é debitado da tarefa principal.",
      submit: "Lançar",
      initial: { task: "", time: "", desc: "" },
      run: (v) => {
        const minutes = parseTimeSpent(v.time);
        if (!(minutes > 0)) throw new Error("Tempo inválido. Use 90, 1h30, 1:30 ou 45m.");
        return api.sideTask(v.task.trim(), minutes, v.desc.trim() || null);
      },
      fields: (v, set) => (
        <>
          <div className="row-fields">
            <Field label="Tarefa">
              <input value={v.task} onChange={set("task")} placeholder="REVIEW-1" required autoFocus />
            </Field>
            <Field label="Tempo">
              <input value={v.time} onChange={set("time")} placeholder="45m, 1h30, 1:30" required />
            </Field>
          </div>
          <Field label="Descrição (opcional)">
            <input value={v.desc} onChange={set("desc")} placeholder="Code review do PR 42" />
          </Field>
        </>
      ),
    },
    {
      id: "end",
      tone: "danger",
      icon: IconStop,
      title: "Finalizar o dia",
      hint: "(opcional horário)",
      modalHint: "Deixe em branco para finalizar agora.",
      submit: "Finalizar",
      initial: { at: "" },
      run: (v) => api.endDay(todayAt(v.at)),
      fields: (v, set) => (
        <Field label="Fim às (opcional)">
          <input type="time" value={v.at} onChange={set("at")} />
        </Field>
      ),
    },
  ];
}

// Quatro botoes grandes; cada um abre um modal com os campos opcionais.
export default function Commands({ status, currentTask, onDone }) {
  const [open, setOpen] = useState(null);
  if (status !== "in_progress" && status !== "paused") return null;

  const actions = actionsFor(status, currentTask);
  const current = actions.find((a) => a.id === open);

  return (
    <>
      <section className="tiles">
        {actions.map((a) => (
          <button key={a.id} className={`tile ${a.tone}`} onClick={() => setOpen(a.id)}>
            <span className="tile-icon">
              <a.icon size={20} />
            </span>
            <span className="tile-title">{a.title}</span>
            <span className="tile-hint">{a.hint}</span>
          </button>
        ))}
      </section>

      {current && (
        <Modal title={current.title} tone={current.tone} onClose={() => setOpen(null)}>
          <p className="muted small">{current.modalHint}</p>
          <ActionForm
            submit={current.submit}
            tone={current.tone}
            initial={current.initial}
            run={current.run}
            onCancel={() => setOpen(null)}
            onDone={async () => {
              setOpen(null);
              await onDone();
            }}
          >
            {current.fields}
          </ActionForm>
        </Modal>
      )}
    </>
  );
}
