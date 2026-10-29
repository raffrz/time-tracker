const pad = (n) => String(n).padStart(2, "0");

export function formatClock(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`;
}

// Horas decimais com virgula, igual a CLI (7h30 -> "7,50").
export function formatDecimalHours(totalSeconds) {
  return (Math.max(0, totalSeconds) / 3600).toFixed(2).replace(".", ",");
}

// Duracao em "H:MM" (ex.: 7h30 -> "7:30"), arredondada ao minuto.
export function formatHoursMinutes(totalSeconds) {
  const m = Math.round(Math.max(0, totalSeconds) / 60);
  return `${Math.floor(m / 60)}:${pad(m % 60)}`;
}

export function formatTime(iso) {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Duracao legivel: 5h 29min, 45min.
export function formatDuration(totalSeconds) {
  const m = Math.floor(Math.max(0, totalSeconds) / 60);
  const h = Math.floor(m / 60);
  if (!h) return `${m}min`;
  return `${h}h ${pad(m % 60)}min`;
}

const WEEKDAYS = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
export function weekday(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return WEEKDAYS[new Date(y, m - 1, d).getDay()];
}

export function greeting(date = new Date()) {
  const h = date.getHours();
  if (h < 12) return "Bom dia";
  if (h < 18) return "Boa tarde";
  return "Boa noite";
}

export function formatDate(isoDate) {
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

// "HH:MM" (input type=time) -> ISO local de hoje, sem fuso: a API assume o horario local.
export function todayAt(hhmm) {
  if (!hhmm) return null;
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${hhmm}:00`;
}

// '90', '1h30', '1h30m', '1:30', '45m' -> minutos (mesmas regras da CLI). NaN se invalido.
export function parseTimeSpent(value) {
  const v = value.trim().toLowerCase();
  if (/^\d+$/.test(v)) return parseInt(v, 10);
  let m = v.match(/^(\d+):(\d{1,2})$/);
  if (m) return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
  m = v.match(/^(?:(\d+)h)?\s*(?:(\d+)m?)?$/);
  if (m && (m[1] || m[2])) return parseInt(m[1] || "0", 10) * 60 + parseInt(m[2] || "0", 10);
  return NaN;
}
