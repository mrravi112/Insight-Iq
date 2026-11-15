import { useEffect, useRef, useState, ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area, LineChart, Line } from "recharts";
import { UploadCloud, Download, X, RefreshCw, Trash2, FileText, AlertTriangle, Sun, Moon } from "lucide-react";
import { api, download, C } from "./api"; import { useApp } from "./App";

const SENT = ["Positive", "Neutral", "Negative"];
const Badge = ({ s }: { s: string }) => <span className={"badge b-" + s}>{s}</span>;
const Skel = () => <div className="grid g3"><div className="skel" /><div className="skel" /><div className="skel" /></div>;
const Card = ({ title, children, sub }: { title?: string; children: ReactNode; sub?: string }) => <section className="card">{title && <h2>{title}</h2>}{sub && <p className="muted" style={{ margin: "2px 0 10px", fontSize: 12 }}>{sub}</p>}{children}</section>;
const Missing = ({ children }: { children: ReactNode }) => <div className="notice info" style={{ marginTop: 10 }}>{children}</div>;
const Err = ({ e }: { e: string }) => <div className="notice" role="alert"><AlertTriangle size={14} style={{ verticalAlign: -2 }} /> {e}</div>;
const Ribbon = ({ d }: { d: any[] }) => <div className="ribbon" role="img" aria-label={d.map(x => `${x.name} ${x.pct}%`).join(", ")}>{d.map(x => <i key={x.name} style={{ width: x.pct + "%", background: C[x.name] }} />)}</div>;

function useData(path: string | null, deps: any[] = []) {
  const [data, setData] = useState<any>(null); const [err, setErr] = useState(""); const [loading, setL] = useState(false);
  useEffect(() => { if (!path) return; let ok = true; setL(true); setErr(""); api(path).then(d => ok && setData(d)).catch(e => ok && (setErr(e.message), setData(null))).finally(() => ok && setL(false)); return () => { ok = false; }; }, [path, ...deps]);
  return { data, err, loading };
}
function Gate({ children, need = true }: { children: (ds: any) => ReactNode; need?: boolean }) {
  const { current, loaded } = useApp();
  if (!loaded) return <Skel />;
  if (!current) return <Onboard />;
  if (current.status !== "completed") return <div className="card"><h2>{current.name} isn't analysed yet</h2><p className="muted">Status: {current.status}{current.error ? ` — ${current.error}` : ""}</p><Link className="btn primary" to="/upload">Go to upload</Link></div>;
  return <>{children(current)}</>;
}
function Onboard() {
  return <div className="hero"><h1 style={{ fontSize: 30 }}>Turn student comments into decisions</h1>
    <p className="muted" style={{ maxWidth: 560 }}>Upload a feedback file, map its columns, and InsightIQ scores sentiment, finds recurring themes, and writes an evidence-linked report. Nothing is shown until you upload your own data.</p>
    <div className="row" style={{ margin: "18px 0" }}>{["Upload CSV, Excel, JSON, TXT, PDF or DOCX", "Confirm column mapping and data checks", "Analyse and explore results"].map((t, i) => <span key={i} className="tag">{i + 1}. {t}</span>)}</div>
    <Link to="/upload" className="btn primary"><UploadCloud />Upload dataset</Link></div>;
}
const Donut = ({ d, h = 240 }: { d: any[]; h?: number }) => <ResponsiveContainer width="100%" height={h}><PieChart><Pie data={d} dataKey="count" nameKey="name" innerRadius="58%" outerRadius="85%" paddingAngle={2}>{d.map(x => <Cell key={x.name} fill={C[x.name]} />)}</Pie><Tooltip formatter={(v: any, n: any, p: any) => [`${v} (${p.payload.pct}%)`, n]} /><Legend /></PieChart></ResponsiveContainer>;
const ax = { tick: { fontSize: 12, fill: "var(--muted)" }, stroke: "var(--border)" };

export function Dashboard() {
  return <Gate>{ds => <DashBody id={ds.id} />}</Gate>;
}
function DashBody({ id }: { id: number }) {
  const { data: d, err, loading } = useData(`/datasets/${id}/dashboard`);
  if (err) return <Err e={err} />; if (loading || !d) return <Skel />;
  const s = Object.fromEntries(d.sentiment.map((x: any) => [x.name, x]));
  const tt = d.topics.filter((t: any) => t.topic !== "Other / Unclassified").slice(0, 10);
  return <div className="grid">
    <div className="grid g6">
      <div className="card kpi"><div className="l">Total responses</div><div className="v">{d.total}</div></div>
      {SENT.map(k => <div key={k} className="card kpi"><div className="l">{k}</div><div className="v" style={{ color: k === "Negative" ? "var(--rose)" : k === "Positive" ? "var(--orange)" : undefined }}>{s[k].pct}%</div><div className="muted" style={{ fontSize: 12 }}>{s[k].count} responses</div></div>)}
      <div className="card kpi small"><div className="l">Most discussed topic</div><div className="v">{d.top_topic?.topic || "—"}</div></div>
      <div className="card kpi"><div className="l">Avg sentiment score</div><div className="v">{d.mean_score}</div><div className="muted" style={{ fontSize: 12 }}>−1 to +1</div></div>
    </div>
    {d.notes.map((n: string) => <Missing key={n}>{n}</Missing>)}
    <div className="grid g2">
      <Card title="Sentiment distribution"><Donut d={d.sentiment} /></Card>
      <Card title="Topic distribution" sub="Mentions per theme; a comment can mention several."><ResponsiveContainer width="100%" height={260}><BarChart data={tt} layout="vertical" margin={{ left: 40 }}><CartesianGrid horizontal={false} stroke="var(--grid-line)" /><XAxis type="number" {...ax} /><YAxis type="category" dataKey="topic" width={150} {...ax} /><Tooltip /><Bar dataKey="count" name="Mentions" fill="var(--orange)" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></Card>
      <Card title="Topic-wise sentiment"><ResponsiveContainer width="100%" height={280}><BarChart data={tt} layout="vertical" margin={{ left: 40 }}><CartesianGrid horizontal={false} stroke="var(--grid-line)" /><XAxis type="number" {...ax} /><YAxis type="category" dataKey="topic" width={150} {...ax} /><Tooltip /><Legend />{SENT.map(k => <Bar key={k} dataKey={k} stackId="a" fill={C[k]} />)}</BarChart></ResponsiveContainer></Card>
      <Card title="Frequently mentioned terms"><ResponsiveContainer width="100%" height={280}><BarChart data={d.terms} layout="vertical" margin={{ left: 20 }}><XAxis type="number" {...ax} /><YAxis type="category" dataKey="term" width={90} {...ax} /><Tooltip /><Bar dataKey="count" fill="var(--chart-dark)" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></Card>
      <Card title="Feedback volume over time">{d.volume ? <ResponsiveContainer width="100%" height={240}><AreaChart data={d.volume}><CartesianGrid stroke="var(--grid-line)" /><XAxis dataKey="period" {...ax} /><YAxis {...ax} allowDecimals={false} label={{ value: "Responses", angle: -90, position: "insideLeft", fontSize: 12 }} /><Tooltip /><Area dataKey="count" name="Responses" stroke="var(--orange)" fill="var(--orange-soft)" /></AreaChart></ResponsiveContainer> : <Missing>Needs a mapped date column with valid dates.</Missing>}</Card>
      <Card title="Sentiment trend">{d.volume && d.volume.length > 1 ? <ResponsiveContainer width="100%" height={240}><LineChart data={d.volume}><CartesianGrid stroke="var(--grid-line)" /><XAxis dataKey="period" {...ax} /><YAxis domain={[-1, 1]} {...ax} /><Tooltip /><Line dataKey="mean_score" name="Mean score" stroke="var(--rose)" strokeWidth={2} dot /></LineChart></ResponsiveContainer> : <Missing>A trend needs feedback across at least two months.</Missing>}</Card>
      <Card title="Course comparison" sub="Share of responses by sentiment">{d.courses.length ? <ResponsiveContainer width="100%" height={260}><BarChart data={d.courses.map((c: any) => ({ name: c.name, ...Object.fromEntries(c.sentiment.map((x: any) => [x.name, x.pct])) }))}><CartesianGrid stroke="var(--grid-line)" vertical={false} /><XAxis dataKey="name" {...ax} /><YAxis unit="%" {...ax} /><Tooltip /><Legend />{SENT.map(k => <Bar key={k} dataKey={k} fill={C[k]} radius={[4, 4, 0, 0]} />)}</BarChart></ResponsiveContainer> : <Missing>Needs a mapped course column.</Missing>}</Card>
      <Card title="Improvement priorities" sub="Ranked by negative mentions × negative share. Not a judgement of anyone's competence.">{d.priorities.length ? d.priorities.map((p: any, i: number) => <div key={p.topic} className="rank"><b className="n">{i + 1}</b><div><b>{p.topic}</b> <span className="muted">{p.negative} of {p.mentions} mentions negative</span><div className="muted" style={{ fontSize: 13 }}>{p.recommendation}</div></div></div>) : <Missing>No topic has two or more negative mentions yet.</Missing>}</Card>
    </div></div>;
}

const STAGES = ["Uploading", "Parsing", "Data validation", "Privacy processing", "Sentiment analysis", "Topic classification", "Report generation", "Analysis completed"];
export function Upload() {
  const { refresh, setCurrent, datasets } = useApp(); const nav = useNavigate(); const cfg = useData("/config");
  const [drag, setDrag] = useState(false); const [up, setUp] = useState<any>(null); const [map, setMap] = useState<any>({}); const [redact, setRedact] = useState(true);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false); const [st, setSt] = useState<any>(null); const [page, setPage] = useState(1); const [q, setQ] = useState(""); const [raw, setRaw] = useState<any>(null);
  const [backend, setBackend] = useState("");
  const timer = useRef<any>();
  useEffect(() => () => clearInterval(timer.current), []);
  useEffect(() => { if (up && !st) api(`/datasets/${up.id}/raw?page=${page}&q=${encodeURIComponent(q)}`).then(setRaw).catch(() => {}); }, [up, page, q]);
  async function send(f: File) {
    setErr(""); const max = (cfg.data?.max_upload_mb || 25) * 1048576;
    if (f.size > max) return setErr(`File is ${(f.size / 1048576).toFixed(1)} MB; the limit is ${cfg.data?.max_upload_mb} MB.`);
    setBusy(true); try { const fd = new FormData(); fd.append("file", f); const r = await api("/datasets/upload", { method: "POST", body: fd }); setUp(r); setMap(r.suggested_mapping); setSt(null); setPage(1); await refresh(); } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  async function start() {
    setErr(""); try { await api(`/datasets/${up.id}/analyze`, { method: "POST", body: JSON.stringify({ mapping: Object.fromEntries(Object.entries(map).filter(([, v]) => v)), redact, sentiment_backend: backend || undefined }) });
      setSt({ status: "processing", stage: "Parsing", progress: 2 }); clearInterval(timer.current);
      timer.current = setInterval(async () => { const s = await api(`/datasets/${up.id}/status`); setSt(s); if (s.status !== "processing") { clearInterval(timer.current); await refresh(); if (s.status === "completed") setCurrent(up.id); } }, 700);
    } catch (e: any) { setErr(e.message); }
  }
  const cols: string[] = up?.columns || []; const unmapped = !map.feedback;
  const cur = st ? Math.max(0, STAGES.indexOf(st.stage)) : -1;
  return <div className="grid">
    {err && <Err e={err} />}
    {!up && <label className={"drop" + (drag ? " on" : "")} onDragOver={e => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); e.dataTransfer.files[0] && send(e.dataTransfer.files[0]); }}>
      <UploadCloud size={34} color="var(--orange)" /><h2 style={{ marginTop: 8 }}>{busy ? "Uploading and parsing…" : "Drop a feedback file here"}</h2>
      <p className="muted">or <span style={{ color: "var(--orange)", fontWeight: 600 }}>choose a file</span> — {cfg.data ? cfg.data.formats.join("  ") : ""}<br />Up to {cfg.data?.max_upload_mb} MB and {cfg.data?.max_records?.toLocaleString()} records</p>
      <input type="file" hidden accept={cfg.data?.formats.join(",")} onChange={e => e.target.files?.[0] && send(e.target.files[0])} /></label>}
    {!up && <Card title="Accepted layouts"><ul className="muted"><li>CSV / Excel / JSON: one row per response; any column names (you confirm the mapping).</li><li>TXT: one comment per line, or blank-line separated multi-line comments, or comments separated by a line of <code>---</code>. Numbering and bullets are stripped.</li><li>PDF / DOCX: tables are extracted if present; otherwise text is split the same way as TXT. Scanned PDFs (images) are not supported. Check the preview before analysing.</li></ul></Card>}
    {up && !st && <>
      <Card title={`Map columns — ${up.filename}`} sub={`${up.rows} rows detected. Auto-detected where names were recognised; nothing is guessed from content.`}>
        {unmapped && <div className="notice" role="alert" style={{ marginBottom: 12 }}>No feedback column was recognised. Choose which column holds the comments{up.ambiguous_text_columns?.length ? ` (long-text candidates: ${up.ambiguous_text_columns.join(", ")})` : ""}.</div>}
        <div className="grid g3">{cfg.data?.fields.map((f: string) => <label key={f}><div className="muted" style={{ fontSize: 12 }}>{f === "feedback" ? "Feedback text (required)" : f === "label" ? "Ground-truth sentiment (optional, for evaluation)" : f}</div>
          <select style={{ width: "100%" }} value={map[f] || ""} onChange={e => setMap({ ...map, [f]: e.target.value })}><option value="">— not mapped —</option>{cols.map(c => <option key={c}>{c}</option>)}</select></label>)}</div>
        <div className="row" style={{ marginTop: 14 }}><label className="row"><input type="checkbox" checked={redact} onChange={e => setRedact(e.target.checked)} /> Redact emails, phone numbers and ID-like codes (names are not detected)</label>
          <label className="row">Sentiment model <select value={backend} onChange={e => setBackend(e.target.value)}><option value="">Server default</option><option value="vader">VADER lexicon</option><option value="transformers">Hugging Face transformer</option></select></label></div>
        <div className="row" style={{ marginTop: 14 }}><button className="btn primary" disabled={unmapped} onClick={start}>Validate and analyse</button><button className="btn" onClick={() => { setUp(null); setRaw(null); }}>Choose another file</button></div>
      </Card>
      <Card title="Preview of extracted records"><div className="row sp" style={{ marginBottom: 8 }}><input type="search" placeholder="Search records…" value={q} onChange={e => { setQ(e.target.value); setPage(1); }} /><span className="muted">{raw?.total ?? "…"} records</span></div>
        {raw && <div className="tablewrap"><table><thead><tr>{raw.columns.map((c: string) => <th key={c} style={c === map.feedback ? { color: "var(--orange)" } : {}}>{c}{c === map.feedback ? " (feedback)" : ""}</th>)}</tr></thead><tbody>{raw.rows.map((r: any, i: number) => <tr key={i}>{raw.columns.map((c: string) => <td key={c}>{String(r[c]).slice(0, 220)}</td>)}</tr>)}</tbody></table></div>}
        <Pager page={page} total={raw?.total || 0} size={25} set={setPage} /></Card></>}
    {st && <Card title={st.status === "completed" ? "Analysis completed" : st.status === "failed" ? "Analysis failed" : st.status === "cancelled" ? "Analysis cancelled" : "Analysing…"}>
      <div className="stages" aria-live="polite">{STAGES.map((s, i) => <div key={s} className={"stage " + (st.status === "completed" || i < cur ? "done" : i === cur && st.status === "processing" ? "cur" : "")}><span className="dot" />{s}</div>)}</div>
      <div className="bar" style={{ margin: "14px 0" }}><div style={{ width: st.progress + "%" }} /></div>
      {st.error && <Err e={st.error} />}
      <div className="row" style={{ marginTop: 10 }}>
        {st.status === "processing" && <button className="btn" onClick={() => api(`/datasets/${up.id}/cancel`, { method: "POST" })}>Cancel</button>}
        {(st.status === "failed" || st.status === "cancelled") && <><button className="btn primary" onClick={start}><RefreshCw />Retry</button><button className="btn" onClick={() => setSt(null)}>Change mapping</button></>}
        {st.status === "completed" && <><button className="btn primary" onClick={() => nav("/")}>Open dashboard</button>
          <div className="muted">{up && qualityLine(datasets, up.id)}</div></>}
      </div></Card>}
  </div>;
}
function qualityLine(datasets: any[], id: number) { const q = datasets.find(d => d.id === id)?.quality; if (!q?.total) return null;
  return <span>{q.accepted} accepted · {q.empty + q.too_short} skipped (empty/too short) · {q.duplicates} duplicates · {q.invalid_dates + q.invalid_ratings} invalid values. {(q.issues || []).join(" ")}</span>; }
function Pager({ page, total, size, set }: any) { const n = Math.max(1, Math.ceil(total / size)); return <div className="row sp" style={{ marginTop: 10 }}><span className="muted">Page {page} of {n}</span><div className="row"><button className="btn" disabled={page <= 1} onClick={() => set(page - 1)}>Previous</button><button className="btn" disabled={page >= n} onClick={() => set(page + 1)}>Next</button></div></div>; }

export function Explorer() { return <Gate>{ds => <ExplorerBody ds={ds} />}</Gate>; }
function ExplorerBody({ ds }: { ds: any }) {
  const [sp] = useSearchParams(); const [f, setF] = useState<any>({ q: sp.get("q") || "", sentiment: "", topic: "", course: "", faculty: "", semester: "", min_rating: "", date_from: "", date_to: "", sort: "id", desc: false }); const [page, setPage] = useState(1); const [open, setOpen] = useState<any>(null);
  useEffect(() => { setF((x: any) => ({ ...x, q: sp.get("q") || "" })); setPage(1); }, [sp]);
  const qs = new URLSearchParams({ page: String(page), size: "25", ...Object.fromEntries(Object.entries(f).filter(([, v]) => v !== "" && v !== false).map(([k, v]) => [k, String(v)])) }).toString();
  const { data, err, loading } = useData(`/datasets/${ds.id}/feedback?${qs}`); const dash = useData(`/datasets/${ds.id}/dashboard`).data;
  const set = (k: string, v: any) => { setF({ ...f, [k]: v }); setPage(1); };
  const uniq = (k: string) => Array.from(new Set((dash?.courses || []).map((c: any) => c.name)));
  return <div className="grid"><Card><div className="row">
    <input type="search" placeholder="Search comments…" value={f.q} onChange={e => set("q", e.target.value)} />
    <select aria-label="Sentiment" value={f.sentiment} onChange={e => set("sentiment", e.target.value)}><option value="">All sentiments</option>{SENT.map(s => <option key={s}>{s}</option>)}</select>
    <select aria-label="Topic" value={f.topic} onChange={e => set("topic", e.target.value)}><option value="">All topics</option>{dash?.topics.map((t: any) => <option key={t.topic}>{t.topic}</option>)}</select>
    <input type="text" placeholder="Course" value={f.course} onChange={e => set("course", e.target.value)} style={{ width: 130 }} />
    <input type="text" placeholder="Faculty" value={f.faculty} onChange={e => set("faculty", e.target.value)} style={{ width: 120 }} />
    <input type="text" placeholder="Semester" value={f.semester} onChange={e => set("semester", e.target.value)} style={{ width: 110 }} />
    <input type="number" placeholder="Min rating" value={f.min_rating} onChange={e => set("min_rating", e.target.value)} style={{ width: 100 }} />
    <input type="date" aria-label="From" value={f.date_from} onChange={e => set("date_from", e.target.value)} /><input type="date" aria-label="To" value={f.date_to} onChange={e => set("date_to", e.target.value)} />
    <select aria-label="Sort" value={f.sort + (f.desc ? "-" : "+")} onChange={e => { const v = e.target.value; setF({ ...f, sort: v.slice(0, -1), desc: v.endsWith("-") }); }}>{["id", "sentiment", "date", "score", "rating"].flatMap(k => [<option key={k + "+"} value={k + "+"}>Sort: {k} ↑</option>, <option key={k + "-"} value={k + "-"}>Sort: {k} ↓</option>])}</select>
    <button className="btn" onClick={() => download(`/datasets/${ds.id}/export?` + new URLSearchParams({ sentiment: f.sentiment, course: f.course, faculty: f.faculty, semester: f.semester, q: f.q }), {}, "feedback.csv").catch(e => alert(e.message))}><Download />Export filtered CSV</button></div></Card>
    {err && <Err e={err} />}
    <Card><div className="muted" style={{ marginBottom: 8 }}>{loading ? "Loading…" : `${data?.total ?? 0} matching responses`}</div>
      <div className="tablewrap"><table><thead><tr><th>Comment</th><th>Sentiment</th><th>Topics</th><th>Score</th><th>Course</th></tr></thead><tbody>
        {data?.items.map((r: any) => <tr key={r.id} className="click" tabIndex={0} onClick={() => setOpen(r)} onKeyDown={e => e.key === "Enter" && setOpen(r)}><td style={{ maxWidth: 420 }}>{r.text}</td><td><Badge s={r.sentiment} /></td>
          <td>{r.topics.map((t: any) => <span key={t.topic} className={"tag " + (t.sentiment || "")}>{t.topic}</span>)}</td><td>{r.score?.toFixed(2)}</td><td>{r.course || "—"}</td></tr>)}</tbody></table></div>
      <Pager page={page} total={data?.total || 0} size={25} set={setPage} /></Card>
    {open && <aside className="drawer" aria-label="Feedback detail"><div className="row sp"><h2>Record analysis</h2><button className="btn" aria-label="Close" onClick={() => setOpen(null)}><X /></button></div>
      <p style={{ fontSize: 15 }}>{open.text}</p><div className="row"><Badge s={open.sentiment} /><span className="muted">score {open.score?.toFixed(3)}</span></div>
      <h3 style={{ marginTop: 16 }}>Topics (clause-level approximation)</h3>{open.topics.map((t: any) => <div key={t.topic} className="row" style={{ margin: "6px 0" }}><span>{t.topic}</span>{t.sentiment ? <Badge s={t.sentiment} /> : <span className="muted">no sentiment</span>}</div>)}
      <h3 style={{ marginTop: 16 }}>Details</h3><p className="muted">Model: {open.model}<br />Confidence: {open.confidence != null ? `${(open.confidence * 100).toFixed(0)}% model probability (uncalibrated)` : "not provided by this model"}<br />Course: {open.course || "—"} · Faculty: {open.faculty || "—"} · Semester: {open.semester || "—"} · Rating: {open.rating ?? "—"}</p></aside>}
  </div>;
}

export function Sentiment() { return <Gate>{ds => <SentBody id={ds.id} />}</Gate>; }
function SentBody({ id }: { id: number }) {
  const { data: d, err } = useData(`/datasets/${id}/sentiment`); if (err) return <Err e={err} />; if (!d) return <Skel />;
  return <div className="grid g2"><Card title="Distribution"><Donut d={d.distribution} /></Card>
    <Card title="Score histogram" sub="Sentiment score from −1 (most negative) to +1 (most positive)."><ResponsiveContainer width="100%" height={240}><BarChart data={d.histogram}><CartesianGrid vertical={false} stroke="var(--grid-line)" /><XAxis dataKey="bin" {...ax} /><YAxis {...ax} allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="var(--orange)" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></Card>
    <Card title="About this model"><p><b>{d.model.sentiment_model}</b></p><p className="muted">{d.model.calibrated_confidence ? "" : "This model does not provide calibrated confidence, so none is displayed. "}Mean score {d.mean_score}. Lexicon-based scoring can miss sarcasm, mixed-language comments and domain-specific phrasing. See Model Evaluation for how to measure accuracy on labeled data.</p></Card></div>;
}

export function Topics() { return <Gate>{ds => <TopicsBody id={ds.id} />}</Gate>; }
function TopicsBody({ id }: { id: number }) {
  const { data: d, err } = useData(`/datasets/${id}/topics`); if (err) return <Err e={err} />; if (!d) return <Skel />;
  return <div className="grid"><Card title="Topic sentiment" sub={d.method}><ResponsiveContainer width="100%" height={420}><BarChart data={d.topics} layout="vertical" margin={{ left: 50 }}><CartesianGrid horizontal={false} stroke="var(--grid-line)" /><XAxis type="number" {...ax} /><YAxis type="category" dataKey="topic" width={170} {...ax} /><Tooltip /><Legend />{SENT.map(k => <Bar key={k} dataKey={k} stackId="a" fill={C[k]} />)}<Bar dataKey="Unscored" stackId="a" fill="var(--neutral)" /></BarChart></ResponsiveContainer></Card>
    <Card title="Recommendations linked to evidence" sub="Shown only where a topic has ≥2 negative mentions. They are prompts for review, not conclusions.">
      {d.priorities.length ? d.priorities.map((p: any) => <div key={p.topic} style={{ padding: "12px 0", borderBottom: "1px solid var(--table-border)" }}><b>{p.topic}</b> <span className="muted">— {p.negative}/{p.mentions} mentions negative ({p.negative_share}%), appears in {p.prevalence}% of comments</span>
        <div>{p.recommendation}</div>{p.evidence.map((e: string, i: number) => <div key={i} className="quote">“{e}”</div>)}</div>) : <Missing>No recommendations: no topic reached the evidence threshold.</Missing>}</Card></div>;
}

export function Groups({ kind }: { kind: "courses" | "faculty" }) { return <Gate>{ds => <GroupBody id={ds.id} kind={kind} />}</Gate>; }
function GroupBody({ id, kind }: { id: number; kind: string }) {
  const { data: d, err } = useData(`/datasets/${id}/${kind}`); const [pick, setPick] = useState<string[]>([]);
  if (err) return <Err e={err} />; if (!d) return <Skel />;
  if (!d.available) return <Missing>No {kind === "courses" ? "course" : "faculty"} column was mapped for this dataset. Re-upload and map that column to enable this page.</Missing>;
  const shown = pick.length ? d.items.filter((x: any) => pick.includes(x.name)) : d.items;
  const toggle = (n: string) => setPick(pick.includes(n) ? pick.filter(x => x !== n) : [...pick, n]);
  return <div className="grid">{d.caution && <div className="notice">{d.caution}</div>}
    <Card title="Compare" sub="Select groups to compare; none selected shows all."><div className="row">{d.items.map((x: any) => <button key={x.name} className={"btn" + (pick.includes(x.name) ? " primary" : "")} onClick={() => toggle(x.name)}>{x.name} <span style={{ opacity: .7 }}>n={x.count}</span></button>)}</div></Card>
    <div className="grid g2">{shown.map((x: any) => <Card key={x.name} title={x.name} sub={`${x.count} responses · mean score ${x.mean_score}${x.rating_mean ? ` · mean rating ${x.rating_mean}` : ""}`}>
      {x.warning && <div className="notice" style={{ marginBottom: 8 }}>{x.warning}</div>}<Ribbon d={x.sentiment} /><div className="row muted" style={{ margin: "6px 0 12px", fontSize: 12 }}>{x.sentiment.map((s: any) => <span key={s.name}>{s.name} {s.pct}% ({s.count})</span>)}</div>
      <h3>Recurring strengths</h3><p>{x.strengths.length ? x.strengths.map((s: string) => <span key={s} className="tag Positive">{s}</span>) : <span className="muted">None met the threshold (≥2 positive mentions).</span>}</p>
      <h3>Improvement opportunities</h3><p>{x.improve.length ? x.improve.map((s: string) => <span key={s} className="tag Negative">{s}</span>) : <span className="muted">None met the threshold (≥2 negative mentions).</span>}</p></Card>)}</div></div>;
}

export function Semesters() { return <Gate>{ds => <SemBody id={ds.id} />}</Gate>; }
function SemBody({ id }: { id: number }) {
  const [a, setA] = useState(""); const [b, setB] = useState(""); const { data: d, err } = useData(`/datasets/${id}/semesters/compare?a=${a}&b=${b}`);
  if (err) return <Err e={err} />; if (!d) return <Skel />; if (!d.comparison) return <Missing>{d.message}</Missing>;
  const c = d.comparison;
  return <div className="grid"><Card><div className="row"><label>From <select value={c.a.name} onChange={e => setA(e.target.value)}>{d.semesters.map((s: string) => <option key={s}>{s}</option>)}</select></label><label>To <select value={c.b.name} onChange={e => setB(e.target.value)}>{d.semesters.map((s: string) => <option key={s}>{s}</option>)}</select></label></div></Card>
    <div className="grid g2">{[c.a, c.b].map((x: any) => <Card key={x.name} title={x.name} sub={`${x.count} responses`}><Ribbon d={x.sentiment} /><div className="row muted" style={{ marginTop: 6, fontSize: 12 }}>{x.sentiment.map((s: any) => <span key={s.name}>{s.name} {s.pct}% ({s.count})</span>)}</div></Card>)}</div>
    <Card title="Negative share by topic" sub="Percent of each topic's mentions that were negative."><ResponsiveContainer width="100%" height={Math.max(260, c.topics.length * 34)}><BarChart data={c.topics} layout="vertical" margin={{ left: 50 }}><CartesianGrid horizontal={false} stroke="var(--grid-line)" /><XAxis type="number" unit="%" {...ax} /><YAxis type="category" dataKey="topic" width={170} {...ax} /><Tooltip /><Legend /><Bar dataKey="neg_pct_a" name={c.a.name} fill="var(--chart-dark)" /><Bar dataKey="neg_pct_b" name={c.b.name} fill="var(--rose)" /></BarChart></ResponsiveContainer></Card>
    <Card title="Topic changes"><div className="tablewrap"><table><thead><tr><th>Topic</th><th>{c.a.name}</th><th>{c.b.name}</th><th>Status</th></tr></thead><tbody>{c.topics.map((t: any) => <tr key={t.topic}><td>{t.topic}</td><td>{t.count_a} mentions{t.neg_pct_a != null && ` · ${t.neg_pct_a}% neg`}</td><td>{t.count_b} mentions{t.neg_pct_b != null && ` · ${t.neg_pct_b}% neg`}</td><td><span className={"tag " + (t.status === "improved" ? "Positive" : t.status === "worse" || t.status === "persisting issue" ? "Negative" : "")}>{t.status}</span></td></tr>)}</tbody></table></div>
      <p className="muted" style={{ fontSize: 12 }}>“Persisting issue” = ≥30% negative in both semesters. Differences of ≤5 points are called stable. Small samples can swing these numbers.</p></Card></div>;
}

export function Reports() { return <Gate>{ds => <ReportBody ds={ds} />}</Gate>; }
function ReportBody({ ds }: { ds: any }) {
  const dash = useData(`/datasets/${ds.id}/dashboard`).data; const [o, setO] = useState<any>({ format: "pdf", course: "", faculty: "", semester: "", topics: [] }); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const courses = dash?.courses.map((c: any) => c.name) || [];
  async function go() { setErr(""); setBusy(true); try { await download(`/datasets/${ds.id}/reports`, { method: "POST", body: JSON.stringify(o) }, `insightiq-report.${o.format}`); } catch (e: any) { setErr(e.message); } finally { setBusy(false); } }
  return <div className="grid">{err && <Err e={err} />}<Card title="Generate report" sub="Statistics come from the analysed data. The summary is extractive and template-based: it quotes counts, not invented prose.">
    <div className="grid g3"><label><div className="muted">Course</div><select style={{ width: "100%" }} value={o.course} onChange={e => setO({ ...o, course: e.target.value })}><option value="">All</option>{courses.map((c: string) => <option key={c}>{c}</option>)}</select></label>
      <label><div className="muted">Faculty</div><input type="text" style={{ width: "100%" }} placeholder="Exact name or blank for all" value={o.faculty} onChange={e => setO({ ...o, faculty: e.target.value })} /></label>
      <label><div className="muted">Semester</div><input type="text" style={{ width: "100%" }} placeholder="e.g. 2026-Spring" value={o.semester} onChange={e => setO({ ...o, semester: e.target.value })} /></label></div>
    <div className="muted" style={{ margin: "12px 0 6px" }}>Limit to topics (optional)</div><div className="row">{dash?.topics.map((t: any) => <button key={t.topic} className={"btn" + (o.topics.includes(t.topic) ? " primary" : "")} onClick={() => setO({ ...o, topics: o.topics.includes(t.topic) ? o.topics.filter((x: string) => x !== t.topic) : [...o.topics, t.topic] })}>{t.topic}</button>)}</div>
    <div className="row" style={{ marginTop: 16 }}><select value={o.format} onChange={e => setO({ ...o, format: e.target.value })}><option value="pdf">PDF report</option><option value="xlsx">Excel workbook</option><option value="csv">CSV (records)</option></select><button className="btn primary" disabled={busy} onClick={go}><FileText />{busy ? "Generating…" : "Generate and download"}</button></div></Card></div>;
}

export function Evaluation() { return <Gate>{ds => <EvalBody id={ds.id} />}</Gate>; }
function EvalBody({ id }: { id: number }) {
  const { data: d, err } = useData(`/datasets/${id}/evaluation`); if (err) return <Err e={err} />; if (!d) return <Skel />; const m = d.metrics;
  return <div className="grid"><Card title="Operational statistics" sub={d.note}><div className="grid g3"><div><div className="muted">Records analysed</div><b style={{ fontSize: 22 }}>{d.records}</b></div><div><div className="muted">Sentiment model</div><b>{d.model_info.sentiment_model}</b></div><div><div className="muted">Topic method</div>{d.model_info.topic_method}</div></div>
    <p className="muted">Processing errors: {d.model_info.errors?.length ? d.model_info.errors.join("; ") : "none recorded"}.</p>{d.quality?.issues?.map((i: string) => <div key={i} className="muted">• {i}</div>)}</Card>
    <Card title="Model evaluation (needs ground truth)">{m ? <><div className="row"><b style={{ fontSize: 22 }}>{(m.accuracy * 100).toFixed(1)}%</b><span className="muted">accuracy on {m.n_labeled} labeled records · macro-F1 {m.macro_f1}</span></div>
      <div className="tablewrap"><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>{m.per_class.map((c: any) => <tr key={c.label}><td>{c.label}</td><td>{c.precision}</td><td>{c.recall}</td><td>{c.f1}</td><td>{c.support}</td></tr>)}</tbody></table></div>
      <h3 style={{ margin: "14px 0 6px" }}>Confusion matrix (rows = true, columns = predicted)</h3><table className="conf" style={{ maxWidth: 420 }}><thead><tr><th></th>{m.labels.map((l: string) => <th key={l}>{l}</th>)}</tr></thead><tbody>{m.confusion.map((r: number[], i: number) => <tr key={i}><th>{m.labels[i]}</th>{r.map((v, j) => <td key={j} style={{ background: i === j ? "var(--orange-soft)" : v ? "var(--rose-soft)" : undefined, fontWeight: i === j ? 700 : 400 }}>{v}</td>)}</tr>)}</tbody></table>
      <p className="muted" style={{ fontSize: 12 }}>Only as trustworthy as the labels. Demo data labels are synthetic.</p></> : <Missing>{d.metrics_message}</Missing>}</Card></div>;
}

export function Privacy() {
  const { datasets, refresh } = useApp();
  return <div className="grid"><Card title="How your data is handled"><ul className="muted"><li>Access: each browser gets a random workspace token; datasets are only readable with it. This is not account-based authentication — use a real login layer before multi-user deployment.</li>
    <li>Raw uploads are kept only until analysis finishes, then deleted. Stored feedback text is the redacted version (if redaction was on).</li><li>Redaction is regex-based: emails, phone numbers, ID-like codes. <b>Names and indirect identifiers are not detected</b>, so results must not be called anonymous without review.</li>
    <li>Course, faculty and semester values are stored as uploaded. Feedback text is not written to server logs.</li><li>Analysis runs locally; no text is sent to external services unless you enable the Hugging Face backend, which downloads model weights once and then runs locally.</li><li>Retention: data stays until you delete it below.</li></ul></Card>
    <Card title="Your datasets">{datasets.length ? <table><thead><tr><th>Name</th><th>Status</th><th>Records</th><th></th></tr></thead><tbody>{datasets.map(d => <tr key={d.id}><td>{d.name}</td><td>{d.status}</td><td>{d.quality?.accepted ?? "—"}</td><td><button className="btn danger" onClick={async () => { if (confirm(`Permanently delete "${d.name}" and all its analysis?`)) { await api(`/datasets/${d.id}`, { method: "DELETE" }); refresh(); } }}><Trash2 />Delete</button></td></tr>)}</tbody></table> : <p className="muted">No datasets stored.</p>}</Card></div>;
}
export function SettingsPage() {
  const { data } = useData("/config");
  const { theme, setTheme } = useApp();
  return <div className="grid">
    <Card title="Appearance" sub="Select your preferred display theme">
      <div className="row" style={{ gap: 14 }}>
        <button
          type="button"
          className={"btn" + (theme === "light" ? " primary" : "")}
          style={{ padding: "12px 20px" }}
          onClick={() => setTheme("light")}
        >
          <Sun size={18} />
          <div style={{ textAlign: "left" }}>
            <div style={{ fontWeight: 600 }}>Light Theme</div>
            <div style={{ fontSize: 11, opacity: 0.85 }}>Daylight palette · Clean & crisp</div>
          </div>
        </button>
        <button
          type="button"
          className={"btn" + (theme === "dark" ? " primary" : "")}
          style={{ padding: "12px 20px" }}
          onClick={() => setTheme("dark")}
        >
          <Moon size={18} />
          <div style={{ textAlign: "left" }}>
            <div style={{ fontWeight: 600 }}>Dark Theme</div>
            <div style={{ fontSize: 11, opacity: 0.85 }}>High contrast · Eye friendly</div>
          </div>
        </button>
      </div>
    </Card>
    <Card title="Server configuration (read-only)" sub="Change these in backend/.env and restart the API.">{data && <table><tbody>{[["Max upload size", data.max_upload_mb + " MB"], ["Max records per dataset", data.max_records], ["Default sentiment backend", data.sentiment_backend], ["Minimum sample for reliable groups", data.min_sample], ["Supported formats", data.formats.join(" ")]].map(([k, v]) => <tr key={k as string}><td className="muted">{k}</td><td>{v}</td></tr>)}</tbody></table>}</Card>
  </div>;
}
