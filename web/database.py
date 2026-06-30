import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Railway provides DATABASE_URL for its Postgres plugin. Fall back to local SQLite.
url = os.environ.get("DATABASE_URL", "sqlite:///./pool.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
