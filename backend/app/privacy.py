import re
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,11}\d(?!\d)"),
    "reg_no": re.compile(r"\b(?:\d{2}[A-Z]{2,4}\d{3,6}|[A-Z]{2,4}[-/]?\d{5,10})\b"),
}
def redact(text: str, enabled: bool = True):
    """Returns (text, n_found). Regex-based: catches emails/phones/ID-like numbers only. Names are NOT detected."""
    n = 0
    for label, rx in PATTERNS.items():
        text, k = rx.subn(f"[{label.upper()}]" if enabled else "\\g<0>", text) if enabled else (text, len(rx.findall(text)))
        n += k
    return text, n
