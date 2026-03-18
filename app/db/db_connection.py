"""
Database connection configuration

"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.global_config import settings

# Create the SQLAlchemy engine using the database URL from settings
engine = create_engine(
    settings.database_url,
    echo=settings.debug_mode, 
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True
    )
# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()

def get_db():
    """Dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database connection and create tables if they don't exist"""
    Base.metadata.create_all(bind=engine)
