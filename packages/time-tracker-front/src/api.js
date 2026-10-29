// Cliente da API do time-tracker (via proxy `/api`, ver vite.config.js).
const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function detailToText(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; "); // erros 422
  return "Erro inesperado.";
}

async function request(method, path, body) {
  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Nao foi possivel conectar a API. Ela esta rodando (python api.py)?", 0);
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(detailToText(data?.detail), res.status);
  return data;
}

export const api = {
  state: () => request("GET", "/days/state"),
  // 409 = nenhum evento no dia ainda; o chamador trata como "sem relatorio".
  report: () => request("GET", "/days/report"),
  dayReport: (workDate) => request("GET", `/days/${workDate}/report`),
  startDay: (task_id, at) => request("POST", "/days/start", { task_id, at }),
  pause: (auto_resume_at, at) => request("POST", "/days/pause", { auto_resume_at, at }),
  resume: (at) => request("POST", "/days/resume", { at }),
  changeTask: (task_id, at) => request("POST", "/days/change-task", { task_id, at }),
  sideTask: (task_id, minutes, description) =>
    request("POST", "/days/side-task", { task_id, minutes, description }),
  endDay: (at) => request("POST", "/days/end", { at }),
  events: (start, end) => {
    const q = new URLSearchParams();
    if (start) q.set("start", start);
    if (end) q.set("end", end);
    const qs = q.toString();
    return request("GET", "/events" + (qs ? `?${qs}` : ""));
  },
  deleteEvent: (id) => request("DELETE", `/events/${id}`),
};
