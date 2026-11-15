import os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv; load_dotenv(BASE / ".env")
except ImportError:
    pass
DATA_DIR = Path(os.getenv("DATA_DIR", BASE / "data")); DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR/'insightiq.db'}")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
MAX_RECORDS = int(os.getenv("MAX_RECORDS", "50000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))
SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "vader")  # vader | transformers
HF_SENTIMENT_MODEL = os.getenv("HF_SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
MIN_SAMPLE = int(os.getenv("MIN_SAMPLE", "20"))  # below this, warn about reliability
ALLOWED_EXT = {".csv", ".xlsx", ".xls", ".json", ".txt", ".pdf", ".docx"}
