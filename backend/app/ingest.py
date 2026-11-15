"""File ingestion: any supported file -> pandas DataFrame of raw records + column detection."""
import io, json, re
from pathlib import Path
import pandas as pd
from .config import MAX_RECORDS

class IngestError(ValueError): pass

ALIASES = {
 "feedback": ["feedback","comment","comments","review","response","student_feedback","student_comment","remarks","text","opinion"],
 "course": ["course","course_name","subject","subject_name","class","paper"],
 "faculty": ["faculty","teacher","instructor","instructor_name","professor","faculty_name","lecturer"],
 "semester": ["semester","term","session","academic_term"],
 "date": ["date","timestamp","submitted","submitted_at","created_at"],
 "rating": ["rating","score","stars","overall_rating"],
 "label": ["label","sentiment","true_sentiment","ground_truth"],
}
def norm(c): return re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")

def detect_mapping(df: pd.DataFrame):
    """Returns (mapping, ambiguous_text_columns). Never guesses a feedback column from content alone."""
    cols = {norm(c): c for c in df.columns}; mapping = {}
    for field, names in ALIASES.items():
        for n in names:
            if n in cols and cols[n] not in mapping.values():
                mapping[field] = cols[n]; break
    text_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and df[c].astype(str).str.len().mean() > 25]
    cand = [c for c in text_cols if norm(c) in ALIASES["feedback"]]
    ambiguous = len(cand) > 1 or ("feedback" not in mapping)
    return mapping, (text_cols if ambiguous else [])

def _text_records(text: str) -> pd.DataFrame:
    text = text.replace("\r\n", "\n")
    if re.search(r"^\s*(-{3,}|={3,})\s*$", text, re.M): parts = re.split(r"^\s*(?:-{3,}|={3,})\s*$", text, flags=re.M)
    elif "\n\n" in text.strip() and sum(1 for l in text.split("\n") if l.strip()) > len(re.split(r"\n\s*\n", text.strip())):
        parts = re.split(r"\n\s*\n", text)            # blank-line separated multi-line comments
    else: parts = text.split("\n")                    # one per line
    out = []
    for p in parts:
        p = re.sub(r"^\s*(?:\d+[.)]|[-*•])\s+", "", " ".join(p.split()))
        out.append(p)
    return pd.DataFrame({"feedback": [p for p in out if p.strip()]})

def parse_file(name: str, raw: bytes) -> pd.DataFrame:
    ext = Path(name).suffix.lower()
    try:
        if ext == ".csv":
            for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
                try: txt = raw.decode(enc); break
                except UnicodeDecodeError: continue
            else: raise IngestError("Could not decode file; save it as UTF-8.")
            try: df = pd.read_csv(io.StringIO(txt), sep=None, engine="python", dtype=str, on_bad_lines="skip")
            except Exception as e: raise IngestError(f"Malformed CSV: {e}")
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(raw), dtype=str)
        elif ext == ".json":
            data = json.loads(raw.decode("utf-8-sig"))
            if isinstance(data, dict):
                data = next((v for v in data.values() if isinstance(v, list)), None) or [data]
            df = pd.json_normalize(data).astype(str).replace("nan", None) if data and isinstance(data[0], dict) else pd.DataFrame({"feedback": [str(x) for x in data]})
        elif ext == ".txt": df = _text_records(raw.decode("utf-8-sig", errors="replace"))
        elif ext == ".pdf":
            import pdfplumber
            tables, texts = [], []
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for pg in pdf.pages:
                    for t in pg.extract_tables():
                        if t and len(t) > 1 and len(t[0]) > 1: tables.append(pd.DataFrame(t[1:], columns=[str(c) for c in t[0]]))
                    texts.append(pg.extract_text() or "")
            df = pd.concat(tables, ignore_index=True) if tables else _text_records("\n".join(texts))
            if df.empty: raise IngestError("No extractable text (scanned PDFs need OCR, which is not supported).")
        elif ext == ".docx":
            import docx
            d = docx.Document(io.BytesIO(raw))
            if d.tables and len(d.tables[0].rows) > 1:
                rows = [[c.text.strip() for c in r.cells] for r in d.tables[0].rows]
                df = pd.DataFrame(rows[1:], columns=rows[0])
            else: df = _text_records("\n".join(p.text for p in d.paragraphs))
        else: raise IngestError(f"Unsupported format '{ext}'.")
    except IngestError: raise
    except Exception as e: raise IngestError(f"Could not read {ext} file: {e}")
    df = df.dropna(how="all").reset_index(drop=True)
    if df.empty: raise IngestError("The file contains no records.")
    if len(df) > MAX_RECORDS: raise IngestError(f"{len(df)} records exceeds the limit of {MAX_RECORDS} (set MAX_RECORDS).")
    df.columns = [str(c) for c in df.columns]
    return df

def clean(df: pd.DataFrame, mapping: dict):
    """Apply mapping, validate. Returns (clean_df, quality dict). Every dropped row is counted by reason."""
    if "feedback" not in mapping or mapping["feedback"] not in df.columns:
        raise IngestError("A feedback text column must be selected.")
    q = {"total": len(df), "accepted": 0, "empty": 0, "too_short": 0, "duplicates": 0, "invalid_dates": 0, "invalid_ratings": 0, "issues": []}
    out = pd.DataFrame({k: df[v] for k, v in mapping.items() if v in df.columns})
    out = out.rename(columns={})
    out["feedback"] = out["feedback"].astype("string").str.strip()
    empty = out["feedback"].isna() | (out["feedback"] == "")
    q["empty"] = int(empty.sum()); out = out[~empty]
    short = out["feedback"].str.len() < 3; q["too_short"] = int(short.sum()); out = out[~short]
    dup = out.duplicated(subset=[c for c in ["feedback","course","faculty","semester"] if c in out], keep="first")
    q["duplicates"] = int(dup.sum()); out = out[~dup]
    if "date" in out:
        d = pd.to_datetime(out["date"], errors="coerce", format="mixed"); q["invalid_dates"] = int((d.isna() & out["date"].notna()).sum()); out["date"] = d
    if "rating" in out:
        r = pd.to_numeric(out["rating"], errors="coerce"); q["invalid_ratings"] = int((r.isna() & out["rating"].notna()).sum()); out["rating"] = r
    if "label" in out:
        lab = out["label"].astype(str).str.strip().str.lower().map({"positive":"Positive","pos":"Positive","neutral":"Neutral","neu":"Neutral","negative":"Negative","neg":"Negative"})
        if lab.isna().any(): q["issues"].append(f"{int(lab.isna().sum())} label values were not Positive/Neutral/Negative and are ignored for evaluation.")
        out["label"] = lab
    q["accepted"] = len(out)
    for k, msg in [("empty","empty or missing feedback text"),("too_short","comments shorter than 3 characters"),("duplicates","duplicate comments"),("invalid_dates","unparseable dates (kept, date left blank)"),("invalid_ratings","non-numeric ratings (kept, rating left blank)")]:
        if q[k]: q["issues"].append(f"{q[k]} {msg}.")
    for f in ("course","faculty","semester"):
        if f not in out: q["issues"].append(f"No '{f}' column mapped: {f}-level analytics are unavailable.")
    if q["accepted"] == 0: raise IngestError("No valid feedback records remain after validation.")
    return out.reset_index(drop=True), q
