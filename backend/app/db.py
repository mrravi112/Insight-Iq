from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from .config import DATABASE_URL
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
def now(): return datetime.now(timezone.utc)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    owner = Column(String(64), index=True, nullable=False)
    name = Column(String(255)); filename = Column(String(255))
    status = Column(String(32), default="uploaded")  # uploaded|processing|completed|failed|cancelled
    stage = Column(String(64), default="Uploaded"); progress = Column(Float, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    columns = Column(JSON, default=list); mapping = Column(JSON, default=dict)
    quality = Column(JSON, default=dict)      # accepted/skipped/duplicates/invalid + issues
    model_info = Column(JSON, default=dict)   # backend, version, errors
    redact = Column(Boolean, default=True)
    cancel = Column(Boolean, default=False)
    feedback = relationship("Feedback", cascade="all, delete-orphan", back_populates="dataset")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    text = Column(Text)                 # redacted text only (if redaction on)
    course = Column(String(255), nullable=True, index=True)
    faculty = Column(String(255), nullable=True, index=True)
    semester = Column(String(64), nullable=True, index=True)
    date = Column(DateTime, nullable=True)
    rating = Column(Float, nullable=True)
    true_label = Column(String(16), nullable=True)
    sentiment = Column(String(16), index=True); score = Column(Float); confidence = Column(Float, nullable=True)
    topics = Column(JSON, default=list)  # [{topic, sentiment, score}]
    pii_found = Column(Integer, default=0)
    model_id = Column(String(128))
    dataset = relationship("Dataset", back_populates="feedback")

def init_db(): Base.metadata.create_all(engine)
