import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# It's a good practice to use environment variables for database credentials
# IMPORTANT: Replace with your actual PostgreSQL username and password
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://edtech_assistant_postgres_db_user:bofCsIxjEjUUKgODlhKgurwVZaEoBLSs@dpg-d2de6q9r0fns73e0vl80-a/edtech_assistant_postgres_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
