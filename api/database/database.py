import os
import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the database credentials from environment variables
DATABASE_USER = os.getenv("POSTGRES_USER", "user")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DATABASE_NAME = os.getenv("POSTGRES_DB", "dbname")
DATABASE_HOST = os.getenv("POSTGRES_HOST", "db")

# Create the database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"

# Create the database engine
engine = _sql.create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = _declarative.declarative_base()
