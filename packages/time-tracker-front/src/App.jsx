import { useState } from "react";
import TodayPage from "./pages/TodayPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import { IconCalendar, IconClock, IconHistory, IconHome, IconMountain } from "./components/Icons.jsx";
import { formatDate, weekday } from "./format.js";
import { useNow } from "./hooks.js";

const PAGES = [
  { id: "today", label: "Hoje", Icon: IconHome, Component: TodayPage },
  { id: "history", label: "Histórico", Icon: IconHistory, Component: HistoryPage },
];

const USER_NAME = import.meta.env.VITE_USER_NAME || "";
const initials = (name) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");

function localIsoDate(ms) {
  const d = new Date(ms);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export default function App() {
  const [page, setPage] = useState("today");
  const Current = PAGES.find((p) => p.id === page).Component;
  const today = localIsoDate(useNow(60000));

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="brand">
          <IconClock size={34} className="brand-icon" />
          <div>
            <div className="brand-name">Horas</div>
            <div className="brand-sub">Trabalho com foco</div>
          </div>
        </div>
        {PAGES.map((p) => (
          <button
            key={p.id}
            className={`nav-item ${page === p.id ? "active" : ""}`}
            onClick={() => setPage(p.id)}
            title={p.label}
          >
            <p.Icon size={20} className="nav-icon" />
            <span className="nav-label">{p.label}</span>
          </button>
        ))}
        <div className="sidebar-quote">
          <IconMountain size={26} />
          <p>Grandes resultados vêm de pequenas consistências.</p>
        </div>
      </nav>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-date">
            <IconCalendar size={20} />
            <div>
              <div>{formatDate(today)}</div>
              <div className="muted small">{weekday(today)}</div>
            </div>
          </div>
          {USER_NAME && <span className="avatar">{initials(USER_NAME)}</span>}
        </header>
        <main className="content">
          <Current />
        </main>
      </div>
    </div>
  );
}
