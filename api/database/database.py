import os
import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm
from dotenv import dotenv_values

# Load environment variables from .env file
env_vars = dotenv_values()

# Retrieve the database credentials from environment variables
DATABASE_USER = env_vars.get("POSTGRES_USER")
DATABASE_PASSWORD = env_vars.get("POSTGRES_PASSWORD")
DATABASE_NAME = env_vars.get("POSTGRES_DB")
print(DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME)
# Create the database connection URL
DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@db/{DATABASE_NAME}"

# Create the database engine
engine = _sql.create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = _declarative.declarative_base()
