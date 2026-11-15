# InsightIQ — Intelligent Feedback Analysis System (CSEAI ML2026-P38)

Upload student feedback (CSV, XLSX/XLS, JSON, TXT, PDF, DOCX), map columns, and get sentiment, multi-label topics, course/faculty/semester analytics, evidence-linked recommendations, and PDF/Excel/CSV reports. FastAPI + SQLite backend, React + TypeScript + Vite + Recharts frontend. Brand colors: Jet Black `#0A0A0A`, Cerulean `#007AB7` / `#38BDF8`, Neon Rose `#FF2D95` / `#FB7185` with full Light and Dark theme support.

## 1. Prerequisites
Python 3.10+, Node 18+. CPU only is fine (4 GB RAM is enough for the default model; the optional transformer needs ~2 GB more and a one-time download).

## 2–5. Install, configure, models, database
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # edit limits/model if wanted
```
* **Database:** SQLite tables are created automatically on first start (`data/insightiq.db`). Set `DATABASE_URL` to a PostgreSQL URL (and `pip install psycopg2-binary`) to switch; no migrations tool is included.
* **Sentiment model:** `SENTIMENT_BACKEND=vader` (default) uses VADER, a lexicon/rule-based model with an academic-domain extension (e.g. "excessive", "too fast"). It is *not* a trained neural network and provides no confidence value. If `vaderSentiment` is missing in a minimal/offline environment, the app uses a clearly identified built-in lexicon fallback (`builtin-lexicon-fallback+academic-extension`); this is a basic fallback, not equivalent to VADER. For a trained model set `SENTIMENT_BACKEND=transformers`, install `transformers torch`, and the first analysis downloads `cardiffnlp/twitter-roberta-base-sentiment-latest` (internet needed once; then offline). Its probabilities are shown as uncalibrated. **The transformer path still requires verification on a machine that can download the model.**
* **Topics:** 14 categories + "Other", assigned by editable regex rules in `app/nlp.py` (`TOPICS`). Multi-label. Each comment is split into clauses at "but/however/although/." and each clause is scored; the clause's sentiment is attributed to topics it mentions. This is an **approximation, not trained aspect-based sentiment**. No zero-shot/embedding classifier is included.
* **Summaries:** extractive and template-based (counts, top topics, representative comments). No LLM is called, so no API key or external data transfer is involved.

## 6–7. Run
```bash
cd backend && uvicorn app.main:app --reload --port 8000     # API docs: http://localhost:8000/docs
cd frontend && npm install && npm run dev                    # http://localhost:5173
```
Tests: `cd backend && pytest -q` (13 tests: parsing, mapping, validation, dedup, PII, topics, full pipeline, report, deletion, access control, error codes).

## 8. Uploading
Upload Feedback → drop a file → confirm the column mapping (the feedback column is never guessed from content; you must choose it if no recognised name exists) → review the searchable preview → *Validate and analyse*. Stages shown come from the backend job status; you can cancel and retry. TXT: one comment per line, or blank-line-separated multi-line comments, or `---` separators. PDF/DOCX: tables first, else text split like TXT. Sample files are in `sample_data/` (synthetic; regenerate with `generate_samples.py`). Limits: `MAX_UPLOAD_MB` (25), `MAX_RECORDS` (50 000).

## 9. Interpreting results
Sentiment score is −1…+1 (positive ≥ 0.05, negative ≤ −0.05). A topic's "negative share" is negative mentions ÷ mentions of that topic. Priorities and recommendations need ≥ 2 negative mentions and show supporting comments. Groups under `MIN_SAMPLE` (20) responses are flagged. **Sentiment is not a measure of teaching competence; faculty are deliberately not ranked.**

## 10. Evaluating the model
Map a column of true Positive/Neutral/Negative labels as "Ground-truth sentiment" at upload; the Model Evaluation page then shows accuracy, per-class precision/recall/F1, macro-F1 and the confusion matrix. Without labels it shows only operational statistics and says so. Topic classification is **not evaluated** (no multi-label metrics implemented). Note: the bundled sample's labels are synthetic and its comments were written in the same vocabulary the lexicon covers, so its high score (~92% in our run) says nothing about real student data.

## 11. Privacy limitations
Access is by a random per-browser token, not user accounts: anyone with the token (or API access to the server) can read the data. Redaction covers emails, phone numbers and ID-like codes only; names are not detected. Raw uploads are deleted after analysis; analysed (redacted) text and course/faculty names remain until you delete the dataset (Privacy & Data page). The upload preview shows the raw file content before redaction.

## 12. Known limitations / troubleshooting
* Not implemented: user accounts/login, topic discovery (BERTopic/LDA), zero-shot topics, editing extracted PDF records before analysis (you can only choose the column and review the preview), OCR for scanned PDFs, per-semester change within faculty pages, Excel export of the PDF's charts, charts inside PDF reports, a notifications area, Tailwind/shadcn (plain CSS was used).
* Analysis runs in a FastAPI background task inside the API process; restarting the server mid-job leaves that dataset as "processing".
* Dashboard aggregation loads a dataset's rows into pandas; fine to tens of thousands of rows, not millions.
* The UI uses the Jet Black / Cerulean Blue / Neon Rose daylight palette and responsive CSS; verify the final layout in a browser after installing frontend dependencies.
* Lexicon sentiment misses sarcasm, negation edge cases and non-English text.
* If the frontend shows network errors, make sure the API is on port 8000 (Vite proxies `/api`).
