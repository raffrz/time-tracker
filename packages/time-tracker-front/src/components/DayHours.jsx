import { useEffect, useState } from "react";
import { api } from "../api.js";
import { formatDecimalHours, formatHoursMinutes } from "../format.js";

// Horas por tarefa de um dia (para apontar na ferramenta da empresa).
// `version` muda quando os eventos sao recarregados, forcando nova leitura.
export default function DayHours({ day, version }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setError(null);
    api
      .dayReport(day)
      .then((r) => alive && setReport(r))
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [day, version]);

  if (error) return <div className="banner error">{error}</div>;
  if (!report) return <p className="muted">Carregando…</p>;

  return (
    <div className="day-hours">
      {report.open_day && (
        <div className="banner warn">Dia não finalizado: horas calculadas até agora.</div>
      )}
      <table className="table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Tarefa</th>
            <th className="num">H:MM</th>
            <th className="num">Horas</th>
          </tr>
        </thead>
        <tbody>
          {report.tasks.map((t) => (
            <tr key={`${t.kind}-${t.task_id}`}>
              <td>
                <span className={`tag ${t.kind}`}>{t.kind === "main" ? "principal" : "side-task"}</span>
              </td>
              <td>{t.task_id}</td>
              <td className="num">{formatHoursMinutes(t.seconds)}</td>
              <td className="num">{formatDecimalHours(t.seconds)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={2}>Total</td>
            <td className="num">{formatHoursMinutes(report.total_seconds)}</td>
            <td className="num">{formatDecimalHours(report.total_seconds)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
