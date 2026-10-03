import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Attempt connection to configured database
# If PostgreSQL is configured, enable pgvector extension
DATABASE_URL = settings.DATABASE_URL

# Helper to determine if we are using PostgreSQL
is_postgres = DATABASE_URL.startswith("postgresql")

try:
    if is_postgres:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"connect_timeout": 3},
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        # Verify connection and install pgvector extension
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        logger.info("Successfully connected to PostgreSQL and initialized pgvector extension.")
    else:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
            pool_pre_ping=True,
        )
except Exception as e:
    logger.warning(
        f"Could not connect to configured database at {DATABASE_URL} ({e}). "
        f"Falling back to local SQLite database with JSON vector compatibility for testing/development."
    )
    fallback_url = "sqlite:///./chatbot_dev.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    is_postgres = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models import conversation, message, document, document_chunk
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
