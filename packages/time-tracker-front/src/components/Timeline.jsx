import { useState } from "react";
import { formatTime } from "../format.js";
import { IconChevronDown, IconClock, IconFlag, IconPause, IconPlay, IconPlus, IconStop, IconSwap } from "./Icons.jsx";

const VISIBLE = 5;

// Converte os eventos do dia em itens da linha do tempo (pausa vira um intervalo).
function buildItems(events, now) {
  const sorted = [...events].sort((a, b) => new Date(a.occurred_at) - new Date(b.occurred_at));
  const items = [];
  let task = null;

  sorted.forEach((e, i) => {
    const at = formatTime(e.occurred_at);
    switch (e.event_type) {
      case "START_DAY":
        task = e.task_id;
        items.push({ id: e.id, tone: "ok", icon: IconPlay, title: "Início do dia", time: at, sub: `Tarefa ${task}` });
        break;
      case "PAUSE": {
        const back = sorted.slice(i + 1).find((x) => x.event_type === "RESUME" || x.event_type === "END_DAY");
        const endMs = back ? new Date(back.occurred_at) : now;
        const mins = Math.round((endMs - new Date(e.occurred_at)) / 60000);
        items.push({
          id: e.id,
          tone: "pause",
          icon: IconPause,
          title: back ? "Pausa" : "Pausa (em andamento)",
          time: `${at} – ${back ? formatTime(back.occurred_at) : "agora"}`,
          sub: `${mins} min`,
        });
        break;
      }
      case "RESUME":
        items.push({ id: e.id, tone: "ok", icon: IconPlay, title: "Retorno", time: at, sub: task && `Tarefa ${task}` });
        break;
      case "CHANGE_TASK":
        task = e.task_id;
        items.push({ id: e.id, tone: "primary", icon: IconSwap, title: "Troca de tarefa", time: at, sub: `Tarefa ${task}` });
        break;
      case "SIDE_TASK":
        items.push({
          id: e.id,
          tone: "side",
          icon: IconPlus,
          title: "Side-task",
          time: `${at} · ${e.minutes} min`,
          sub: [e.task_id, e.description].filter(Boolean).join(" - "),
        });
        break;
      case "END_DAY":
        items.push({ id: e.id, tone: "danger", icon: IconStop, title: "Fim do dia", time: at });
        break;
      default:
        break;
    }
  });
  return items;
}

export default function Timeline({ events, now }) {
  const [expanded, setExpanded] = useState(false);
  const items = buildItems(events, now);
  const shown = expanded ? items : items.slice(0, VISIBLE);

  return (
    <section className="panel">
      <h2 className="panel-title">
        <IconClock size={22} /> Linha do tempo
      </h2>
      {items.length === 0 ? (
        <p className="muted small timeline-empty">
          <IconFlag size={16} /> Nenhum registro hoje.
        </p>
      ) : (
        <ol className="timeline">
          {shown.map((it) => (
            <li key={it.id} className={`tl-item ${it.tone}`}>
              <span className="tl-dot">
                <it.icon size={13} />
              </span>
              <div className="tl-body">
                <div className="tl-title">{it.title}</div>
                <div className="tl-time">{it.time}</div>
                {it.sub && <div className="tl-sub">{it.sub}</div>}
              </div>
            </li>
          ))}
        </ol>
      )}
      {items.length > VISIBLE && (
        <button className="link-btn" onClick={() => setExpanded((v) => !v)}>
          <IconChevronDown size={16} style={{ transform: expanded ? "rotate(180deg)" : undefined }} />
          {expanded ? "Ver menos" : `Ver mais (${items.length - VISIBLE})`}
        </button>
      )}
    </section>
  );
}
