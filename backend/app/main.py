import io, json, logging, os, pickle
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends, BackgroundTasks, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from . import config, analytics as an, reports
from .db import init_db, SessionLocal, Dataset, Feedback
from .ingest import parse_file, detect_mapping, clean, IngestError, ALIASES
from .nlp import get_sentiment, classify
from .privacy import redact

log = logging.getLogger("insightiq")  # never log feedback text
app = FastAPI(title="InsightIQ API", version="1.0", description="Feedback analysis for course and faculty evaluation.")

cors_env = os.getenv("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "name": "InsightIQ API", "version": "1.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

RAW = config.DATA_DIR / "raw"; RAW.mkdir(exist_ok=True)
@app.on_event("startup")
def _s(): init_db()

def db():
    s = SessionLocal()
    try: yield s
    finally: s.close()
def owner(x_owner_token: str = Header(None)):
    if not x_owner_token or len(x_owner_token) < 16: raise HTTPException(401, "Missing or invalid X-Owner-Token header.")
    return x_owner_token
def get_ds(dataset_id: int, s=Depends(db), o=Depends(owner)) -> Dataset:
    ds = s.get(Dataset, dataset_id)
    if not ds or ds.owner != o: raise HTTPException(404, "Dataset not found.")   # 404 for others' data: no existence leak
    return ds
def completed(ds):
    if ds.status != "completed": raise HTTPException(409, f"Analysis is '{ds.status}'; results are only available for completed datasets.")
    return ds
def frame(s, ds, **flt):
    q = s.query(Feedback).filter(Feedback.dataset_id == ds.id)
    for k, v in flt.items():
        if v: q = q.filter(getattr(Feedback, k) == v)
    rows = q.all(); return rows, an.to_df(rows)

def summary(ds):
    return {"id": ds.id, "name": ds.name, "filename": ds.filename, "status": ds.status, "stage": ds.stage, "progress": ds.progress,
            "error": ds.error, "created_at": ds.created_at.isoformat(), "columns": ds.columns, "mapping": ds.mapping, "quality": ds.quality, "model_info": ds.model_info}

@app.get("/api/config")
def cfg(): return {"max_upload_mb": config.MAX_UPLOAD_MB, "max_records": config.MAX_RECORDS, "formats": sorted(config.ALLOWED_EXT), "min_sample": config.MIN_SAMPLE,
                   "sentiment_backend": config.SENTIMENT_BACKEND, "fields": list(ALIASES)}

@app.post("/api/datasets/upload", status_code=201)
async def upload(file: UploadFile = File(...), s=Depends(db), o=Depends(owner)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXT: raise HTTPException(415, f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(config.ALLOWED_EXT))}")
    raw = await file.read()
    if len(raw) > config.MAX_UPLOAD_MB * 1024 * 1024: raise HTTPException(413, f"File exceeds {config.MAX_UPLOAD_MB} MB limit.")
    try: df = parse_file(file.filename, raw)
    except IngestError as e: raise HTTPException(422, str(e))
    mapping, ambiguous = detect_mapping(df)
    ds = Dataset(owner=o, name=Path(file.filename).stem, filename=file.filename, columns=list(df.columns), mapping=mapping)
    s.add(ds); s.commit()
    (RAW / f"{ds.id}.pkl").write_bytes(pickle.dumps(df))
    return {**summary(ds), "rows": len(df), "suggested_mapping": mapping, "needs_feedback_column": "feedback" not in mapping, "ambiguous_text_columns": ambiguous,
            "preview": json.loads(df.head(20).fillna("").to_json(orient="records"))}

@app.get("/api/datasets/{dataset_id}/raw")
def raw_page(page: int = 1, size: int = 25, q: str = "", ds=Depends(get_ds)):
    p = RAW / f"{ds.id}.pkl"
    if not p.exists(): raise HTTPException(410, "Raw upload was already discarded after analysis.")
    df = pickle.loads(p.read_bytes())
    if q: df = df[df.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    return {"total": len(df), "columns": list(df.columns), "rows": json.loads(df.iloc[(page-1)*size:page*size].fillna("").to_json(orient="records"))}

@app.get("/api/datasets")
def list_ds(s=Depends(db), o=Depends(owner)):
    return [summary(d) for d in s.query(Dataset).filter(Dataset.owner == o).order_by(Dataset.id.desc()).all()]
@app.get("/api/datasets/{dataset_id}")
def one(ds=Depends(get_ds)): return summary(ds)
@app.get("/api/datasets/{dataset_id}/status")
def status(ds=Depends(get_ds)): return {k: summary(ds)[k] for k in ("id", "status", "stage", "progress", "error")}

def _set(s, ds, **kw):
    for k, v in kw.items(): setattr(ds, k, v)
    s.commit()

def run_analysis(ds_id: int, mapping: dict, redact_on: bool, backend: Optional[str]):
    s = SessionLocal(); ds = s.get(Dataset, ds_id)
    try:
        _set(s, ds, status="processing", stage="Parsing", progress=5, error=None, cancel=False, mapping=mapping, redact=redact_on)
        df = pickle.loads((RAW / f"{ds_id}.pkl").read_bytes())
        _set(s, ds, stage="Data validation", progress=12)
        cdf, q = clean(df, mapping)
        _set(s, ds, stage="Privacy processing", progress=20, quality=q)
        pii = cdf["feedback"].apply(lambda t: redact(t, redact_on)); texts = [p[0] for p in pii]; pii_n = [p[1] for p in pii]
        if sum(pii_n): q["issues"].append(f"{sum(pii_n)} identifier-like patterns (email/phone/ID) found in {sum(1 for x in pii_n if x)} comments" + (" and redacted." if redact_on else "; redaction is OFF."))
        _set(s, ds, quality=dict(q), stage="Sentiment analysis", progress=25)
        m = get_sentiment(backend)
        s.query(Feedback).filter(Feedback.dataset_id == ds_id).delete()
        B = config.BATCH_SIZE; n = len(texts); errors = []
        for i in range(0, n, B):
            s.refresh(ds)
            if ds.cancel: s.query(Feedback).filter(Feedback.dataset_id == ds_id).delete(); _set(s, ds, status="cancelled", stage="Cancelled"); return
            chunk = texts[i:i+B]; sc = m.score(chunk)
            _set(s, ds, stage="Topic classification" if i else "Sentiment analysis", progress=25 + 65 * (i + B) / n)
            for j, (t, (lab, score, conf)) in enumerate(zip(chunk, sc)):
                r = cdf.iloc[i + j]; g = lambda k: (None if k not in cdf or pd.isna(r[k]) else r[k])
                s.add(Feedback(dataset_id=ds_id, text=t, course=g("course"), faculty=g("faculty"), semester=g("semester"), date=g("date"), rating=g("rating"),
                               true_label=g("label"), sentiment=lab, score=float(score), confidence=conf, topics=classify(t, m), pii_found=pii_n[i + j], model_id=m.model_id))
            s.commit()
        _set(s, ds, stage="Report generation", progress=95)
        _set(s, ds, model_info={"sentiment_model": m.model_id, "calibrated_confidence": m.calibrated_confidence, "topic_method": "keyword-rule multi-label + clause-level sentiment (approximation)", "errors": errors},
             status="completed", stage="Analysis completed", progress=100)
        (RAW / f"{ds_id}.pkl").unlink(missing_ok=True)   # discard raw (possibly identifying) upload
    except IngestError as e: _set(s, ds, status="failed", stage="Failed", error=str(e))
    except Exception as e:
        log.exception("analysis failed for dataset %s", ds_id); _set(s, ds, status="failed", stage="Failed", error=f"{type(e).__name__}: {e}")
    finally: s.close()

@app.post("/api/datasets/{dataset_id}/analyze", status_code=202)
def analyze(bg: BackgroundTasks, body: dict = Body(...), ds=Depends(get_ds)):
    if ds.status == "processing": raise HTTPException(409, "Already processing.")
    if not (RAW / f"{ds.id}.pkl").exists(): raise HTTPException(410, "Raw upload no longer available; upload the file again.")
    mapping = body.get("mapping") or {}
    if "feedback" not in mapping: raise HTTPException(422, "mapping.feedback is required.")
    bg.add_task(run_analysis, ds.id, mapping, bool(body.get("redact", True)), body.get("sentiment_backend"))
    return {"id": ds.id, "status": "processing"}
@app.post("/api/datasets/{dataset_id}/cancel")
def cancel(s=Depends(db), ds=Depends(get_ds)):
    if ds.status != "processing": raise HTTPException(409, "Not processing."); 
    _set(s, ds, cancel=True); return {"cancelling": True}

@app.get("/api/datasets/{dataset_id}/dashboard")
def dash(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds); return an.dashboard(df)
@app.get("/api/datasets/{dataset_id}/feedback")
def feedback(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=200), q: str = "", sentiment: str = "", topic: str = "", course: str = "", faculty: str = "",
             semester: str = "", min_rating: Optional[float] = None, date_from: str = "", date_to: str = "", sort: str = "id", desc: bool = False, s=Depends(db), ds=Depends(get_ds)):
    completed(ds); Q = s.query(Feedback).filter(Feedback.dataset_id == ds.id)
    for col, v in (("sentiment", sentiment), ("course", course), ("faculty", faculty), ("semester", semester)):
        if v: Q = Q.filter(getattr(Feedback, col) == v)
    if q: Q = Q.filter(Feedback.text.ilike(f"%{q}%"))
    if min_rating is not None: Q = Q.filter(Feedback.rating >= min_rating)
    if date_from: Q = Q.filter(Feedback.date >= pd.to_datetime(date_from))
    if date_to: Q = Q.filter(Feedback.date <= pd.to_datetime(date_to))
    if sort not in ("id", "sentiment", "date", "score", "rating"): raise HTTPException(422, "Invalid sort column.")
    col = getattr(Feedback, sort); Q = Q.order_by(col.desc() if desc else col.asc())
    rows = Q.all()
    if topic: rows = [r for r in rows if any(t["topic"] == topic for t in r.topics or [])]
    tot = len(rows); rows = rows[(page-1)*size:page*size]
    return {"total": tot, "page": page, "size": size, "items": [{"id": r.id, "text": r.text, "sentiment": r.sentiment, "score": r.score, "confidence": r.confidence, "topics": r.topics,
            "course": r.course, "faculty": r.faculty, "semester": r.semester, "date": r.date.isoformat() if r.date else None, "rating": r.rating, "model": r.model_id} for r in rows]}
@app.get("/api/datasets/{dataset_id}/sentiment")
def sentiment(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds)
    bins = pd.cut(df["score"], [-1, -.6, -.2, .05, .4, .7, 1.0001], labels=["≤-0.6", "-0.6…-0.2", "-0.2…0.05", "0.05…0.4", "0.4…0.7", ">0.7"]).value_counts().sort_index()
    return {"distribution": an.sent_dist(df), "histogram": [{"bin": str(k), "count": int(v)} for k, v in bins.items()], "mean_score": round(df.score.mean(), 3), "model": ds.model_info}
@app.get("/api/datasets/{dataset_id}/topics")
def topics(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds); return {"topics": an.topic_table(df), "priorities": an.priorities(df), "method": ds.model_info.get("topic_method")}
@app.get("/api/datasets/{dataset_id}/courses")
def courses(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds); return {"items": an.group_stats(df, "course"), "available": bool(df.course.notna().any())}
@app.get("/api/datasets/{dataset_id}/faculty")
def faculty(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds); return {"items": an.group_stats(df, "faculty"), "available": bool(df.faculty.notna().any()),
        "caution": "Sentiment is not a measure of teaching competence; do not rank faculty by it. Compare only groups with comparable, sufficient sample sizes."}
@app.get("/api/datasets/{dataset_id}/semesters/compare")
def sem(a: str = "", b: str = "", s=Depends(db), ds=Depends(get_ds)):
    completed(ds); _, df = frame(s, ds); sems = sorted(df.semester.dropna().unique().tolist())
    if len(sems) < 2: return {"semesters": sems, "comparison": None, "message": "Needs at least two distinct values in a mapped semester column. Add a 'semester' column (e.g. 2025-Fall) and re-upload."}
    a, b = a or sems[0], b or sems[-1]; return {"semesters": sems, "comparison": an.compare(df, a, b)}
@app.get("/api/datasets/{dataset_id}/evaluation")
def evaluation(s=Depends(db), ds=Depends(get_ds)):
    completed(ds); rows, df = frame(s, ds)
    out = {"records": len(df), "sentiment": an.sent_dist(df), "topics": an.topic_table(df), "model_info": ds.model_info, "quality": ds.quality,
           "note": "Operational statistics only describe what the model output; they do not measure accuracy.", "metrics": None}
    lab = df.dropna(subset=["label"])
    if len(lab) >= 10:
        L = ["Positive", "Neutral", "Negative"]; p, r, f, sup = precision_recall_fscore_support(lab.label, lab.sentiment, labels=L, zero_division=0)
        out["metrics"] = {"n_labeled": len(lab), "accuracy": round(accuracy_score(lab.label, lab.sentiment), 4), "labels": L,
            "per_class": [{"label": l, "precision": round(p[i], 3), "recall": round(r[i], 3), "f1": round(f[i], 3), "support": int(sup[i])} for i, l in enumerate(L)],
            "macro_f1": round(float(f.mean()), 3), "confusion": confusion_matrix(lab.label, lab.sentiment, labels=L).tolist()}
    else: out["metrics_message"] = "No ground-truth sentiment labels (or fewer than 10). Map a 'label' column (Positive/Neutral/Negative) at upload to compute accuracy, precision, recall, F1 and a confusion matrix. Topic classification cannot be evaluated without multi-label ground truth."
    return out

@app.post("/api/datasets/{dataset_id}/reports")
def report(body: dict = Body(default={}), s=Depends(db), ds=Depends(get_ds)):
    completed(ds); flt = {k: body.get(k) for k in ("course", "faculty", "semester")}
    rows, df = frame(s, ds, **flt)
    if body.get("topics"): df = df[df.topics.apply(lambda ts: any(t["topic"] in body["topics"] for t in ts))]
    if df.empty: raise HTTPException(422, "No records match the selected scope.")
    scope = ", ".join(f"{k}={v}" for k, v in flt.items() if v) or "complete dataset"; fmt = body.get("format", "pdf")
    if fmt == "pdf": return Response(reports.pdf(ds, df, scope), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="insightiq-report-{ds.id}.pdf"'})
    ids = set(df.id); rows = [r for r in rows if r.id in ids]
    if fmt == "xlsx": return Response(reports.xlsx(ds, df, rows), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="insightiq-{ds.id}.xlsx"'})
    if fmt == "csv": return Response(reports.records_df(rows).to_csv(index=False), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="insightiq-{ds.id}.csv"'})
    raise HTTPException(422, "format must be pdf, csv or xlsx")
@app.get("/api/datasets/{dataset_id}/export")
def export(sentiment: str = "", course: str = "", faculty: str = "", semester: str = "", q: str = "", s=Depends(db), ds=Depends(get_ds)):
    completed(ds); rows, _ = frame(s, ds, sentiment=sentiment, course=course, faculty=faculty, semester=semester)
    if q: rows = [r for r in rows if q.lower() in r.text.lower()]
    return Response(reports.records_df(rows).to_csv(index=False), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="feedback.csv"'})
@app.delete("/api/datasets/{dataset_id}", status_code=204)
def delete(s=Depends(db), ds=Depends(get_ds)):
    (RAW / f"{ds.id}.pkl").unlink(missing_ok=True); s.delete(ds); s.commit()
