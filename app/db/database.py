from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config.config import settings

# Define a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create a SQLAlchemy engine using the database URL from settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Create a session factory for database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Dependency function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()