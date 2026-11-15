import io, time, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os, tempfile
os.environ["DATA_DIR"] = tempfile.mkdtemp()
from fastapi.testclient import TestClient
from app.main import app
from app.ingest import parse_file, detect_mapping, clean, IngestError
from app.privacy import redact
from app.nlp import classify, get_sentiment
import pandas as pd

SAMPLES = Path(__file__).resolve().parents[2] / "sample_data"
A = {"X-Owner-Token": "a" * 20}; B = {"X-Owner-Token": "b" * 20}

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c: yield c

def run(client, name, data, mapping=None, hdr=A, **extra):
    r = client.post("/api/datasets/upload", files={"file": (name, data)}, headers=hdr); assert r.status_code == 201, r.text
    j = r.json(); body = {"mapping": mapping or j["suggested_mapping"], **extra}
    assert client.post(f"/api/datasets/{j['id']}/analyze", json=body, headers=hdr).status_code == 202
    for _ in range(100):
        st = client.get(f"/api/datasets/{j['id']}/status", headers=hdr).json()
        if st["status"] in ("completed", "failed"): break
        time.sleep(.1)
    return j["id"], st

def test_csv_parsing_and_mapping():
    df = parse_file("a.csv", b"Student_Comment,Subject\nGood class,Math\n")
    assert "Student_Comment" in df.columns
    m, amb = detect_mapping(pd.DataFrame({"student_feedback": ["x" * 40], "course_name": ["c"]}))
    assert m["feedback"] == "student_feedback" and m["course"] == "course_name"

def test_unknown_columns_never_guessed():
    m, amb = detect_mapping(pd.DataFrame({"foo": ["a long unrecognised text column " * 3], "bar": ["b"]}))
    assert "feedback" not in m and "foo" in amb

def test_excel_alt_columns():
    df = parse_file("x.xlsx", (SAMPLES / "sample_feedback_alt_columns.xlsx").read_bytes())
    m, _ = detect_mapping(df); assert m["feedback"] == "student_comment" and m["faculty"] == "instructor_name"

def test_txt_formats():
    assert len(parse_file("a.txt", b"one\ntwo\nthree\n")) == 3
    assert len(parse_file("a.txt", b"first line\ncontinues\n\nsecond one\n")) == 2
    assert len(parse_file("a.txt", b"a comment\n---\nanother comment\n")) == 2

def test_malformed_and_empty():
    with pytest.raises(IngestError): parse_file("a.csv", b"")
    with pytest.raises(IngestError): parse_file("a.json", b"{not json")
    with pytest.raises(IngestError): parse_file("a.xyz", b"x")

def test_validation_counts_every_drop():
    df = pd.DataFrame({"f": ["Great teacher", "Great teacher", "", None, "ok", "Fine course"], "d": ["2025-01-01", "2025-01-01", "bad", "x", "y", "z"]})
    c, q = clean(df, {"feedback": "f", "date": "d"})
    assert q["accepted"] == 2 and q["duplicates"] == 1 and q["empty"] == 2 and q["too_short"] == 1 and q["total"] == 6
    with pytest.raises(IngestError): clean(df[["d"]].assign(f=None), {"feedback": "f"})

def test_pii_redaction():
    t, n = redact("mail me at jo.doe@uni.edu or +91 98765 43210, roll 21CSE1234")
    assert "@" not in t and "98765" not in t and n >= 3
    assert redact("no pii here")[1] == 0

def test_multilabel_topic_sentiment():
    r = {x["topic"]: x["sentiment"] for x in classify("The teacher explains concepts clearly, but the teaching pace is too fast.", get_sentiment())}
    assert r["Teaching Clarity"] == "Positive" and r["Teaching Pace"] == "Negative"
    assert classify("Hello world", get_sentiment())[0]["topic"] == "Other / Unclassified"

def test_full_pipeline_dashboard_eval_report_delete(client):
    i, st = run(client, "s.csv", (SAMPLES / "sample_feedback.csv").read_bytes()); assert st["status"] == "completed", st
    d = client.get(f"/api/datasets/{i}/dashboard", headers=A).json()
    q = client.get(f"/api/datasets/{i}", headers=A).json()["quality"]
    assert q["total"] == 84 and q["accepted"] + q["duplicates"] == 84 and d["total"] == q["accepted"] and abs(sum(x["pct"] for x in d["sentiment"]) - 100) < .3 and d["courses"] and d["volume"]
    f = client.get(f"/api/datasets/{i}/feedback?sentiment=Negative&size=5", headers=A).json()
    assert f["total"] > 0 and all(x["sentiment"] == "Negative" for x in f["items"])
    c = client.get(f"/api/datasets/{i}/semesters/compare", headers=A).json(); assert c["comparison"]["topics"]
    e = client.get(f"/api/datasets/{i}/evaluation", headers=A).json(); assert e["metrics"]["n_labeled"] == q["accepted"] and len(e["metrics"]["confusion"]) == 3
    r = client.post(f"/api/datasets/{i}/reports", json={"format": "pdf", "course": "Databases"}, headers=A); assert r.content[:4] == b"%PDF"
    assert client.post(f"/api/datasets/{i}/reports", json={"format": "xlsx"}, headers=A).status_code == 200
    assert b"feedback" in client.get(f"/api/datasets/{i}/export?sentiment=Positive", headers=A).content
    assert client.delete(f"/api/datasets/{i}", headers=A).status_code == 204
    assert client.get(f"/api/datasets/{i}", headers=A).status_code == 404

def test_no_dates_or_semesters_reported_not_invented(client):
    i, st = run(client, "t.txt", b"The teacher explains clearly\nAssignments are excessive\nLabs were useful\n")
    assert st["status"] == "completed"
    d = client.get(f"/api/datasets/{i}/dashboard", headers=A).json()
    assert "volume" not in d and d["courses"] == [] and any("date" in n for n in d["notes"])
    assert client.get(f"/api/datasets/{i}/semesters/compare", headers=A).json()["comparison"] is None

def test_pii_is_not_stored(client):
    i, _ = run(client, "p.txt", (SAMPLES / "sample_feedback.txt").read_bytes())
    items = client.get(f"/api/datasets/{i}/feedback?size=200", headers=A).json()["items"]
    assert not any("student@uni.edu" in x["text"] or "9876543210" in x["text"] for x in items)
    assert client.get(f"/api/datasets/{i}/raw", headers=A).status_code == 410   # raw upload discarded

def test_access_control_and_errors(client):
    i, _ = run(client, "o.txt", b"great course here\nbad pace of lectures\n")
    assert client.get(f"/api/datasets/{i}/dashboard", headers=B).status_code == 404
    assert client.delete(f"/api/datasets/{i}", headers=B).status_code == 404
    assert client.get(f"/api/datasets/{i}/dashboard").status_code == 401
    assert client.post("/api/datasets/upload", files={"file": ("x.exe", b"MZ")}, headers=A).status_code == 415
    assert client.post("/api/datasets/upload", files={"file": ("x.csv", b"")}, headers=A).status_code == 422
    r = client.post("/api/datasets/upload", files={"file": ("u.csv", b"foo,bar\nsome text,1\n")}, headers=A).json()
    assert r["needs_feedback_column"]
    assert client.post(f"/api/datasets/{r['id']}/analyze", json={"mapping": {}}, headers=A).status_code == 422
    assert client.get(f"/api/datasets/{r['id']}/dashboard", headers=A).status_code == 409   # incomplete ≠ completed

def test_wrong_column_failure_is_reported(client):
    r = client.post("/api/datasets/upload", files={"file": ("u.csv", b"foo,bar\nsome text,1\n")}, headers=A).json()
    client.post(f"/api/datasets/{r['id']}/analyze", json={"mapping": {"feedback": "nope"}}, headers=A); time.sleep(.5)
    st = client.get(f"/api/datasets/{r['id']}/status", headers=A).json(); assert st["status"] == "failed" and st["error"]
