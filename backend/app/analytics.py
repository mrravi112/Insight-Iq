import re
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from .config import MIN_SAMPLE
from .nlp import OTHER

STOP = set(ENGLISH_STOP_WORDS) | {"course","class","sir","madam","teacher","faculty","really","also","would","could","one","get","like","lot","bit"}
REC = {  # topic -> recommendation shown only when negative evidence exists
 "Teaching Pace": "Review the pace of difficult lectures; add short recap points or slower walkthroughs for complex topics.",
 "Teaching Clarity": "Add worked examples and check understanding more often for complex concepts.",
 "Subject Knowledge": "Consider faculty development support or guest sessions where depth is requested.",
 "Course Content": "Review syllabus relevance and update outdated material.",
 "Teaching Methodology": "Mix lecture formats (examples, case studies, interactive activities).",
 "Faculty Support": "Improve availability and approachability (fixed office hours, quicker responses).",
 "Doubt Resolution": "Introduce regular doubt-clearing sessions.",
 "Practical Learning": "Increase hands-on, lab or project time linked to theory.",
 "Assignment Workload": "Review assignment volume and deadline spacing.",
 "Assessment and Examinations": "Review assessment alignment, grading transparency and feedback turnaround.",
 "Learning Resources": "Improve access to notes, readings, and recordings.",
 "Course Organization": "Improve scheduling, structure and communication of the plan.",
 "Classroom Environment": "Check classroom facilities (audio-visual, seating, noise).",
 "Student Engagement": "Add interactive or discussion-based activities to raise engagement.",
}

def to_df(rows):
    df = pd.DataFrame([{"id": r.id, "text": r.text, "course": r.course, "faculty": r.faculty, "semester": r.semester,
        "date": r.date, "rating": r.rating, "sentiment": r.sentiment, "score": r.score, "label": r.true_label,
        "topics": r.topics or [], "pii": r.pii_found} for r in rows])
    return df

def pct(n, d): return round(100 * n / d, 1) if d else 0.0
def sent_dist(df):
    c = df["sentiment"].value_counts(); n = len(df)
    return [{"name": s, "count": int(c.get(s, 0)), "pct": pct(c.get(s, 0), n)} for s in ("Positive", "Neutral", "Negative")]

def topic_table(df):
    rec = {}
    for ts in df["topics"]:
        for t in ts:
            r = rec.setdefault(t["topic"], {"topic": t["topic"], "count": 0, "Positive": 0, "Neutral": 0, "Negative": 0, "Unscored": 0})
            r["count"] += 1; r[t["sentiment"] or "Unscored"] += 1
    return sorted(rec.values(), key=lambda r: -r["count"])

def terms(df, k=15):
    c = Counter(w for t in df["text"] for w in re.findall(r"[a-z]{3,}", t.lower()) if w not in STOP)
    return [{"term": w, "count": n} for w, n in c.most_common(k)]

def group_stats(df, col):
    out = []
    for name, g in df.dropna(subset=[col]).groupby(col):
        n = len(g); d = sent_dist(g); tt = topic_table(g)
        row = {"name": name, "count": n, "sentiment": d, "mean_score": round(g["score"].mean(), 3),
               "topics": tt[:8], "reliable": n >= MIN_SAMPLE,
               "warning": None if n >= MIN_SAMPLE else f"Only {n} responses (<{MIN_SAMPLE}); treat as indicative, not conclusive.",
               "strengths": [t["topic"] for t in tt if t["Positive"] >= 2 and t["Positive"] > t["Negative"] and t["topic"] != OTHER][:4],
               "improve": [t["topic"] for t in tt if t["Negative"] >= 2 and t["Negative"] >= t["Positive"] and t["topic"] != OTHER][:4]}
        if g["rating"].notna().any(): row["rating_mean"] = round(g["rating"].mean(), 2)
        out.append(row)
    return sorted(out, key=lambda r: -r["count"])

def priorities(df, limit=6):
    n = len(df); tt = topic_table(df); out = []
    for t in tt:
        if t["topic"] == OTHER or t["Negative"] < 2: continue
        out.append({"topic": t["topic"], "negative": t["Negative"], "mentions": t["count"], "negative_share": pct(t["Negative"], t["count"]),
                    "prevalence": pct(t["count"], n), "recommendation": REC.get(t["topic"], ""),
                    "evidence": df[df["topics"].apply(lambda ts: any(x["topic"] == t["topic"] and x["sentiment"] == "Negative" for x in ts))]["text"].head(3).tolist()})
    return sorted(out, key=lambda r: -(r["negative"] * r["negative_share"]))[:limit]

def dashboard(df):
    n = len(df); d = sent_dist(df); tt = topic_table(df); real = [t for t in tt if t["topic"] != OTHER]
    out = {"total": n, "sentiment": d, "mean_score": round(df["score"].mean(), 3),
           "top_topic": real[0] if real else None, "topics": tt, "terms": terms(df), "priorities": priorities(df), "notes": []}
    if df["date"].notna().sum() >= 2:
        s = df.dropna(subset=["date"]).assign(m=lambda x: x["date"].dt.to_period("M").astype(str))
        out["volume"] = [{"period": p, "count": len(g), "mean_score": round(g["score"].mean(), 3)} for p, g in s.groupby("m")]
    else: out["notes"].append("Feedback volume and trend charts need a mapped date column with valid dates.")
    out["courses"] = group_stats(df, "course") if df["course"].notna().any() else []
    if not out["courses"]: out["notes"].append("Course comparison needs a mapped course column.")
    out["has_faculty"] = bool(df["faculty"].notna().any()); out["has_semester"] = bool(df["semester"].notna().any())
    if n < MIN_SAMPLE: out["notes"].append(f"Only {n} responses: results are indicative, not statistically reliable.")
    return out

def compare(df, a, b):
    A, B = df[df.semester == a], df[df.semester == b]
    if A.empty or B.empty: return None
    ta, tb = {t["topic"]: t for t in topic_table(A)}, {t["topic"]: t for t in topic_table(B)}
    rows = []
    for t in sorted(set(ta) | set(tb)):
        x, y = ta.get(t), tb.get(t)
        sa = pct(x["Negative"], x["count"]) if x else None; sb = pct(y["Negative"], y["count"]) if y else None
        rows.append({"topic": t, "count_a": x["count"] if x else 0, "count_b": y["count"] if y else 0, "neg_pct_a": sa, "neg_pct_b": sb,
                     "status": "new" if not x else "dropped" if not y else "persisting issue" if (sa or 0) >= 30 and (sb or 0) >= 30 else "improved" if sb < sa - 5 else "worse" if sb > sa + 5 else "stable"})
    return {"a": {"name": a, "count": len(A), "sentiment": sent_dist(A)}, "b": {"name": b, "count": len(B), "sentiment": sent_dist(B)}, "topics": rows}
