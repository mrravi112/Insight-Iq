import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  UploadCloud,
  Table2,
  Smile,
  Tags,
  BookOpen,
  Users,
  GitCompare,
  FileText,
  FlaskConical,
  ShieldCheck,
  Settings as Cog,
  Search,
  Menu,
  UserRound,
  Sun,
  Moon
} from "lucide-react";
import { api } from "./api";
import * as P from "./pages";

export type ThemeMode = "light" | "dark";

type Ctx = {
  datasets: any[];
  current: any;
  setCurrent: (id: number) => void;
  refresh: () => Promise<void>;
  loaded: boolean;
  theme: ThemeMode;
  toggleTheme: () => void;
  setTheme: (t: ThemeMode) => void;
};
export const AppCtx = createContext<Ctx>(null as any);
export const useApp = () => useContext(AppCtx);

const NAV = [
  ["/", "Dashboard", LayoutDashboard],
  ["/upload", "Upload Feedback", UploadCloud],
  ["/explorer", "Feedback Explorer", Table2],
  ["/sentiment", "Sentiment Analysis", Smile],
  ["/topics", "Topic Analysis", Tags],
  ["/courses", "Course Analytics", BookOpen],
  ["/faculty", "Faculty Analytics", Users],
  ["/semesters", "Semester Comparison", GitCompare],
  ["/reports", "AI-Generated Reports", FileText],
  ["/evaluation", "Model Evaluation", FlaskConical],
  ["/privacy", "Privacy & Data", ShieldCheck],
  ["/settings", "Settings", Cog]
] as any[];

export default function App() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [sel, setSel] = useState<number | null>(Number(localStorage.getItem("iq_ds")) || null);
  const [loaded, setLoaded] = useState(false);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [prof, setProf] = useState(false);
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("iq_theme") as ThemeMode | null;
    if (saved === "dark" || saved === "light") return saved;
    return typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  const loc = useLocation();
  const nav = useNavigate();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("iq_theme", theme);
  }, [theme]);

  const setTheme = (t: ThemeMode) => setThemeState(t);
  const toggleTheme = () => setThemeState(prev => (prev === "light" ? "dark" : "light"));

  const refresh = useCallback(async () => {
    try {
      const d = await api("/datasets");
      setDatasets(d);
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => setOpen(false), [loc.pathname]);

  const current = datasets.find(d => d.id === sel) || datasets.find(d => d.status === "completed") || datasets[0] || null;
  const setCurrent = (id: number) => {
    setSel(id);
    localStorage.setItem("iq_ds", String(id));
  };
  const title = NAV.find(n => n[0] === loc.pathname)?.[1] || "InsightIQ";

  return (
    <AppCtx.Provider value={{ datasets, current, setCurrent, refresh, loaded, theme, toggleTheme, setTheme }}>
      <div className="app">
        <aside className={"side" + (open ? " open" : "")} aria-label="Primary">
          <div className="brand">
            <span className="mark" aria-hidden />
            <span>InsightIQ</span>
          </div>
          <nav className="nav">
            {NAV.map(([to, label, Icon]) => (
              <NavLink key={to} to={to} end={to === "/"}>
                <Icon aria-hidden />
                {label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <div className="main">
          <header className="top">
            <button className="btn menu-btn" aria-label="Open navigation" onClick={() => setOpen(!open)}>
              <Menu />
            </button>
            <h2 style={{ whiteSpace: "nowrap" }}>{title}</h2>
            <form
              className="search"
              role="search"
              onSubmit={e => {
                e.preventDefault();
                nav("/explorer?q=" + encodeURIComponent(q));
              }}
            >
              <Search size={16} color="var(--muted)" aria-hidden />
              <input
                aria-label="Search feedback"
                placeholder="Search feedback…"
                value={q}
                onChange={e => setQ(e.target.value)}
              />
            </form>
            <span className="grow" />
            <select
              aria-label="Select dataset"
              value={current?.id || ""}
              onChange={e => setCurrent(Number(e.target.value))}
              style={{ maxWidth: 220 }}
            >
              {!datasets.length && <option value="">No datasets yet</option>}
              {datasets.map(d => (
                <option key={d.id} value={d.id}>
                  {d.name} · {d.status}
                </option>
              ))}
            </select>
            <button
              className="btn theme-btn"
              type="button"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              onClick={toggleTheme}
            >
              {theme === "light" ? <Moon size={15} /> : <Sun size={15} />}
              <span className="theme-btn-text" style={{ fontSize: 13, fontWeight: 550 }}>
                {theme === "light" ? "Dark" : "Light"}
              </span>
            </button>
            <div style={{ position: "relative" }}>
              <button className="btn" aria-label="Profile menu" onClick={() => setProf(!prof)}>
                <UserRound />
              </button>
              {prof && (
                <div className="card" style={{ position: "absolute", right: 0, top: 44, width: 260, zIndex: 9 }}>
                  <h3>Anonymous workspace</h3>
                  <p className="muted" style={{ fontSize: 12 }}>
                    Your data is tied to a random token stored in this browser. There are no accounts; clearing it makes
                    your datasets unreachable.
                  </p>
                  <button
                    className="btn danger"
                    onClick={() => {
                      if (confirm("Forget this workspace token? Existing datasets will become inaccessible.")) {
                        localStorage.removeItem("iq_token");
                        localStorage.removeItem("iq_ds");
                        location.href = "/";
                      }
                    }}
                  >
                    Reset workspace
                  </button>
                </div>
              )}
            </div>
          </header>
          <main className="content">
            {current && loc.pathname !== "/upload" && loc.pathname !== "/privacy" && loc.pathname !== "/settings" && (
              <div className="row" style={{ marginBottom: 16 }}>
                <span className="muted">Viewing</span>
                <b>{current.name}</b>
                <span
                  className={
                    "badge b-" +
                    (current.status === "completed"
                      ? "Positive"
                      : current.status === "failed"
                      ? "Negative"
                      : "Neutral")
                  }
                >
                  {current.status}
                </span>
                {current.model_info?.sentiment_model && (
                  <span className="muted">· {current.model_info.sentiment_model}</span>
                )}
              </div>
            )}
            <Routes>
              <Route path="/" element={<P.Dashboard />} />
              <Route path="/upload" element={<P.Upload />} />
              <Route path="/explorer" element={<P.Explorer />} />
              <Route path="/sentiment" element={<P.Sentiment />} />
              <Route path="/topics" element={<P.Topics />} />
              <Route path="/courses" element={<P.Groups kind="courses" />} />
              <Route path="/faculty" element={<P.Groups kind="faculty" />} />
              <Route path="/semesters" element={<P.Semesters />} />
              <Route path="/reports" element={<P.Reports />} />
              <Route path="/evaluation" element={<P.Evaluation />} />
              <Route path="/privacy" element={<P.Privacy />} />
              <Route path="/settings" element={<P.SettingsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </AppCtx.Provider>
  );
}
