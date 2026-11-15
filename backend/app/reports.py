import io, datetime as dt
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from . import analytics as an
BLACK, BLUE, ROSE = colors.HexColor("#0A0A0A"), colors.HexColor("#007AB7"), colors.HexColor("#FF2D95")

def build_content(ds, df, scope):
    d = an.dashboard(df); n = len(df); s = {x["name"]: x for x in d["sentiment"]}
    top = d["top_topic"]["topic"] if d["top_topic"] else "n/a"
    strengths = [t for t in d["topics"] if t["Positive"] >= 2 and t["Positive"] > t["Negative"] and t["topic"] != "Other / Unclassified"][:5]
    summary = (f"{n} responses analysed ({scope}). {s['Positive']['pct']}% positive, {s['Neutral']['pct']}% neutral, {s['Negative']['pct']}% negative. "
               f"Most discussed theme: {top}. " + (f"Top improvement priority: {d['priorities'][0]['topic']} ({d['priorities'][0]['negative']} negative mentions)." if d["priorities"] else "No topic reached the threshold of 2 negative mentions."))
    return {"summary": summary, "dash": d, "strengths": strengths, "scope": scope}

def pdf(ds, df, scope):
    c = build_content(ds, df, scope); d = c["dash"]
    buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=44, bottomMargin=40, title="InsightIQ Report")
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Title"], textColor=BLACK, alignment=0, fontSize=22)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=BLUE, spaceBefore=12)
    B = ParagraphStyle("b", parent=ss["BodyText"], leading=14)
    def tbl(rows, widths=None):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), BLUE), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTSIZE", (0,0), (-1,-1), 8.5),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#E5E7EB")), ("VALIGN", (0,0), (-1,-1), "TOP")])); return t
    P = lambda t, st=B: Paragraph(str(t).replace("&", "&amp;").replace("<", "&lt;"), st)
    mi = ds.model_info or {}
    E = [P("InsightIQ — Feedback Analysis Report", H1),
         P(f"Dataset: {ds.name} · Scope: {scope} · Records: {len(df)} · Generated: {dt.datetime.now():%Y-%m-%d %H:%M} · Sentiment model: {mi.get('sentiment_model')}", B),
         P("1. Executive summary", H2), P(c["summary"]),
         P("2. Dataset overview & 3. Data quality", H2)]
    q = ds.quality or {}
    E += [tbl([["Total rows","Accepted","Empty","Too short","Duplicates"], [q.get("total"), q.get("accepted"), q.get("empty"), q.get("too_short"), q.get("duplicates")]])]
    E += [P(i) for i in q.get("issues", [])]
    E += [P("4. Sentiment analysis", H2), tbl([["Sentiment","Count","%"]] + [[x["name"], x["count"], x["pct"]] for x in d["sentiment"]])]
    E += [P("5. Topic analysis", H2), tbl([["Topic","Mentions","Pos","Neu","Neg"]] + [[t["topic"], t["count"], t["Positive"], t["Neutral"], t["Negative"]] for t in d["topics"]])]
    E += [P("6. Key strengths", H2)] + ([P(f"• {t['topic']}: {t['Positive']} positive vs {t['Negative']} negative mentions") for t in c["strengths"]] or [P("No theme met the threshold (≥2 positive mentions, more positive than negative).")])
    E += [P("7–8. Areas for improvement and evidence-based recommendations", H2)]
    for p in d["priorities"]:
        E += [P(f"• {p['topic']} — {p['negative']} of {p['mentions']} mentions negative ({p['negative_share']}%). Recommendation: {p['recommendation']}"),
              *[P(f"   “{e[:220]}”", ParagraphStyle("q", parent=B, textColor=colors.HexColor("#626B76"), leftIndent=14)) for e in p["evidence"]]]
    if not d["priorities"]: E += [P("No topic reached 2 negative mentions; no recommendations generated.")]
    E += [P("9. Semester comparison", H2), P("Use the Semester Comparison page; see CSV/Excel export for per-record data." if d["has_semester"] else "Unavailable: no semester column was mapped.")]
    E += [P("10. Model limitations", H2), P("Sentiment: " + str(mi.get("sentiment_model")) + ". The default model is lexicon-based (not a trained neural model) and has no calibrated confidence. Topic labels come from keyword rules; topic sentiment is a clause-level approximation. Predictions are unvalidated unless labeled data was evaluated. Sentiment is not a measure of faculty competence.")]
    E += [P("11. Privacy notes", H2), P(f"Redaction {'enabled' if ds.redact else 'disabled'}. Regex redaction covers emails, phone numbers and ID-like codes only; names and indirect identifiers are not detected, so anonymity is not guaranteed. {int(df['pii'].sum())} identifier-like patterns were found.")]
    doc.build(E); return buf.getvalue()

def records_df(rows, redact=True):
    return pd.DataFrame([{"id": r.id, "feedback": r.text, "course": r.course, "faculty": r.faculty, "semester": r.semester, "date": r.date,
        "rating": r.rating, "sentiment": r.sentiment, "score": r.score, "topics": "; ".join(f"{t['topic']}:{t['sentiment'] or 'n/a'}" for t in (r.topics or [])), "model": r.model_id} for r in rows])

def xlsx(ds, df, rows):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        records_df(rows).to_excel(w, sheet_name="Feedback", index=False)
        pd.DataFrame(an.topic_table(df)).to_excel(w, sheet_name="Topics", index=False)
        pd.DataFrame(an.sent_dist(df)).to_excel(w, sheet_name="Sentiment", index=False)
    return buf.getvalue()
