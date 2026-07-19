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

# Create the database engine.
#
# Pool sizing is per OS process and env-tunable. Production runs 4 uvicorn workers, each
# with its own engine, so the cluster-wide ceiling is workers * (pool_size + max_overflow).
# With the defaults below that is 4 * (5 + 5) = 40 connections steady state. This leaves
# generous headroom under postgres's default max_connections (100) minus reserved superuser
# slots (~3): even during a rolling deploy where an old and new worker set briefly coexist
# (8 * 10 = 80) it stays under the ceiling, and there is still room for psql/backups/monitoring.
# Bump DB_POOL_SIZE / DB_MAX_OVERFLOW per deployment if a worker legitimately needs more
# concurrent connections, but keep workers * (pool_size + max_overflow) well under the server
# max_connections for your worst-case worker count. pool_pre_ping transparently replaces
# connections dropped by a DB container restart; pool_recycle avoids handing out very stale
# connections.
def _pool_int(name: str, default: int, minimum: int) -> int:
    """Read a non-negative pool-sizing int from the environment, clamped to `minimum`.
    A non-numeric value falls back to `default` rather than crashing engine creation."""
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


DB_POOL_SIZE = _pool_int("DB_POOL_SIZE", 5, minimum=1)
DB_MAX_OVERFLOW = _pool_int("DB_MAX_OVERFLOW", 5, minimum=0)

engine = _sql.create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Create a session factory
SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = _declarative.declarative_base()
