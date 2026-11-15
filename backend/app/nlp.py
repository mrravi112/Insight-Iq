"""Replaceable NLP pipeline. Each analyzer reports exactly which model produced its output."""
import re
from .config import SENTIMENT_BACKEND, HF_SENTIMENT_MODEL, BATCH_SIZE

POS, NEU, NEG = "Positive", "Neutral", "Negative"

class VaderSentiment:
    """Lexicon- and rule-based model (VADER). NOT a trained neural model; no calibrated confidence."""
    model_id = "vaderSentiment-lexicon+academic-extension"; calibrated_confidence = False
    # Domain extension: VADER's stock lexicon misses common academic complaints. Documented in README.
    EXTRA = {"excessive": -2.2, "rushed": -1.8, "sluggish": -1.5, "tedious": -1.8, "outdated": -2.0, "overloaded": -2.2,
             "disorganized": -2.2, "disorganised": -2.2, "unclear": -1.8, "confusing": -1.8, "heavy": -1.2, "irrelevant": -1.8,
             "unhelpful": -2.2, "monotonous": -2.0, "lacking": -1.5, "insufficient": -1.8, "unresponsive": -2.2, "clear": 1.5,
             "clearly": 1.5, "informative": 2.0, "approachable": 2.0, "knowledgeable": 2.2, "organized": 1.5, "organised": 1.5}
    PHRASES = [(r"\btoo (fast|quick|quickly)\b", "rushed"), (r"\btoo slow(ly)?\b", "sluggish"), (r"\btoo (much|many)\b", "excessive"),
               (r"\btoo (long|lengthy)\b", "tedious"), (r"\bnot (clear|helpful|enough|good)\b", "unclear")]
    def __init__(self):
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.a = SentimentIntensityAnalyzer()
            self.a.lexicon.update(self.EXTRA)
            self.model_id = "vaderSentiment-lexicon+academic-extension"
            self._fallback = False
        except ImportError:
            # Offline/minimal-environment fallback. Explicitly named so the UI and reports
            # never imply that VADER (or a neural model) was loaded when it was not.
            self.a = None
            self.model_id = "builtin-lexicon-fallback+academic-extension"
            self._fallback = True
        self.calibrated_confidence = False
        self._fallback_words = {
            "excellent": 2.4, "great": 1.8, "good": 1.4, "helpful": 1.8, "useful": 1.5,
            "clear": 1.5, "clearly": 1.5, "amazing": 2.4, "love": 2.0, "enjoy": 1.7,
            "informative": 2.0, "approachable": 2.0, "knowledgeable": 2.2, "organized": 1.5,
            "organised": 1.5, "excellent": 2.4, "bad": -1.8, "poor": -1.8, "worst": -2.5,
            "hate": -2.2, "boring": -1.7, "confusing": -1.8, "unclear": -1.8,
            "excessive": -2.2, "rushed": -1.8, "sluggish": -1.5, "tedious": -1.8,
            "outdated": -2.0, "overloaded": -2.2, "disorganized": -2.2, "disorganised": -2.2,
            "irrelevant": -1.8, "unhelpful": -2.2, "monotonous": -2.0, "lacking": -1.5,
            "insufficient": -1.8, "unresponsive": -2.2, "late": -0.8, "difficult": -0.7,
            "fast": -0.5, "slow": -0.4, "supportive": 1.8, "friendly": 1.4,
        }
    def _prep(self, t):
        for rx, rep in self.PHRASES: t = re.sub(rx, rep, t, flags=re.I)
        return t
    def score(self, texts):
        out = []
        for t in texts:
            t = self._prep(t)
            if self.a is not None:
                c = self.a.polarity_scores(t)["compound"]
            else:
                words = re.findall(r"[a-z']+", t.lower())
                vals = []
                negate = False
                for i, word in enumerate(words):
                    if word in {"not", "never", "no", "hardly", "isn't", "wasn't", "doesn't", "don't"}:
                        negate = True
                        continue
                    v = self.EXTRA.get(word, self._fallback_words.get(word, 0.0))
                    if negate and v:
                        v *= -0.8
                        negate = False
                    if v:
                        vals.append(v)
                raw = sum(vals) / (len(vals) ** 0.5) if vals else 0.0
                c = max(-1.0, min(1.0, raw / 4.0))
            out.append((POS if c >= 0.05 else NEG if c <= -0.05 else NEU, c, None))
        return out

class HFSentiment:
    """Hugging Face text-classification model (default: cardiffnlp twitter-roberta). Needs `pip install transformers torch`
    and a one-time model download. Softmax probabilities are NOT calibrated and are exposed only as 'model probability'."""
    calibrated_confidence = False
    def __init__(self, model=HF_SENTIMENT_MODEL):
        from transformers import pipeline
        self.model_id = model
        self.p = pipeline("text-classification", model=model, top_k=None, truncation=True, max_length=256)
    def score(self, texts):
        out = []
        for res in self.p(list(texts), batch_size=BATCH_SIZE):
            d = {r["label"].lower(): r["score"] for r in res}
            pos, neg = d.get("positive", d.get("label_2", 0)), d.get("negative", d.get("label_0", 0))
            top = max(res, key=lambda r: r["score"])
            lab = {"positive": POS, "label_2": POS, "negative": NEG, "label_0": NEG}.get(top["label"].lower(), NEU)
            out.append((lab, float(pos - neg), float(top["score"])))
        return out

_cache = {}
def get_sentiment(backend=None):
    backend = backend or SENTIMENT_BACKEND
    if backend not in _cache:
        _cache[backend] = HFSentiment() if backend == "transformers" else VaderSentiment()
    return _cache[backend]

# ---- Topic classification: transparent, configurable keyword/phrase rules (multi-label). Not a trained classifier. ----
TOPICS = {
 "Teaching Pace": r"\b(pace|paced|speed|too fast|too slow|rush(ed|ing)?|hurr(y|ied)|slow(ly)?|fast|rapid(ly)?)\b",
 "Teaching Clarity": r"\b(explain(s|ed|ing)?|explanation|clear(ly)?|unclear|understand|understandable|confus(ed|ing)|concept(s)?|easy to follow|lucid|vague)\b",
 "Subject Knowledge": r"\b(knowledg(e|eable)|expert(ise)?|command over|well[- ]versed|depth|experience[d]?|know(s)? (the )?subject)\b",
 "Course Content": r"\b(content|syllabus|curriculum|topics?|outdated|relevant|relevance|coverage|material covered)\b",
 "Teaching Methodology": r"\b(method(ology)?|teaching style|approach|lecture(s)?|slides?|case stud(y|ies)|demonstrat\w+|examples?|interactive)\b",
 "Faculty Support": r"\b(support(ive)?|helpful|approachable|friendly|rude|available|availability|mentor\w*|encourag\w+|respond(s|ed)?|polite|supportive|caring|cooperative)\b",
 "Doubt Resolution": r"\b(doubts?|questions?|clarif(y|ied|ication)|query|queries|ask(ing)?|clear(ed|ing)? (my )?doubts?)\b",
 "Practical Learning": r"\b(practical(s)?|lab(s)?|hands[- ]on|project(s)?|real[- ]world|industry|application(s)?|experiment(s)?|coding|implementation)\b",
 "Assignment Workload": r"\b(assignment(s)?|homework|workload|deadline(s)?|submission(s)?|too much work|excessive|overload\w*|burden\w*)\b",
 "Assessment and Examinations": r"\b(exam(s|ination(s)?)?|test(s)?|quiz(zes)?|grad(e|es|ing)|marks?|evaluation|assessment|paper|question paper|internals?)\b",
 "Learning Resources": r"\b(resource(s)?|notes|textbook(s)?|reference(s)?|material(s)?|recording(s)?|library|reading|e-?learning|videos?)\b",
 "Course Organization": r"\b(organi[sz]ed|organi[sz]ation|schedule(d)?|timetable|structure[d]?|planning|planned|punctual\w*|late|cancel(l)?ed|disorgani[sz]ed|well[- ]planned|time ?management)\b",
 "Classroom Environment": r"\b(classroom|environment|atmosphere|noise|noisy|seating|projector|ventilation|infrastructure|wifi|ac|facilities|class (is|was) (crowded|comfortable))\b",
 "Student Engagement": r"\b(engag\w+|interest(ing|ed)?|boring|bored|motivat\w+|participat\w+|discussion(s)?|attention|enthusias\w+|dull|inspir\w+|activities)\b",
}
_RX = {k: re.compile(v, re.I) for k, v in TOPICS.items()}
OTHER = "Other / Unclassified"
_SPLIT = re.compile(r"(?<=[.!?;])\s+|\s*,?\s+\b(?:but|however|although|though|yet|whereas|while|except)\b\s*|\s+\bwhile\b\s+", re.I)

def clauses(text): return [c.strip() for c in _SPLIT.split(text) if c and c.strip() and len(c.strip()) > 2]

def classify(text, sent_model):
    """Multi-label topics with clause-level sentiment. Approximation: each clause is scored by the sentiment model
    and attributed to the topics whose keywords it contains. This is NOT trained aspect-based sentiment analysis."""
    cl = clauses(text) or [text]
    scores = sent_model.score(cl)
    found = {}
    for c, (lab, sc, _) in zip(cl, scores):
        for t, rx in _RX.items():
            if rx.search(c): found.setdefault(t, []).append((lab, sc))
    res = []
    for t, v in found.items():
        avg = sum(s for _, s in v) / len(v)
        res.append({"topic": t, "sentiment": POS if avg >= 0.05 else NEG if avg <= -0.05 else NEU, "score": round(avg, 4)})
    return res or [{"topic": OTHER, "sentiment": None, "score": None}]
