import os
import sys
import shutil
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Determine database path absolute relative to database.py directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DB_PATH = os.path.join(BASE_DIR, "literacy.db")

def is_readonly_env():
    """Detect Vercel, AWS Lambda, or any read-only filesystem environment."""
    if os.name == 'nt':
        return False
    return (
        os.getenv("VERCEL") in ("1", "true", "True", "yes")
        or "VERCEL" in os.environ
        or "VERCEL_ENV" in os.environ
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "LAMBDA_TASK_ROOT" in os.environ
    )

IS_SERVERLESS_OR_READONLY = is_readonly_env()

if IS_SERVERLESS_OR_READONLY and not os.getenv("DATABASE_URL"):
    print("[CRITICAL PERSISTENCE WARNING] Running in serverless environment without persistent DATABASE_URL environment variable.")
    print("[CRITICAL PERSISTENCE WARNING] Ephemeral /tmp database will reset on cold starts. Set DATABASE_URL (e.g., PostgreSQL on Supabase/Neon/Render) for serverless persistence.")
    TMP_DB_PATH = "/tmp/literacy.db"
    if not os.path.exists(TMP_DB_PATH) and os.path.exists(ORIGINAL_DB_PATH):
        try:
            shutil.copy2(ORIGINAL_DB_PATH, TMP_DB_PATH)
            print(f"[INFO] Initialized temporary database copy at {TMP_DB_PATH}")
        except Exception as e:
            print(f"[WARN] Failed to copy literacy.db to /tmp: {e}")
    DB_PATH = TMP_DB_PATH
else:
    DB_PATH = ORIGINAL_DB_PATH

# Normalize path for cross-platform SQLite URI format
normalized_db_path = os.path.abspath(DB_PATH).replace("\\", "/")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{normalized_db_path}")

# Standardize postgres scheme for SQLAlchemy 1.4/2.0 compatibility
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure PostgreSQL driver compatibility for serverless runtimes
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://") and "+" not in SQLALCHEMY_DATABASE_URL.split("://")[0]:
    try:
        import pg8000
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
    except Exception:
        try:
            import psycopg2
        except Exception:
            try:
                import psycopg
                SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
            except Exception:
                pass

# Configure connection parameters for SQLite vs PostgreSQL
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
is_pg8000 = "pg8000" in SQLALCHEMY_DATABASE_URL

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 30}
elif is_pg8000:
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args = {"ssl_context": ssl_ctx}

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
        "pool_timeout": 30,
    })

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_kwargs
)

# Configure SQLite PRAGMAs for concurrent execution and performance
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            if IS_SERVERLESS_OR_READONLY:
                cursor.execute("PRAGMA journal_mode=DELETE")
            else:
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        except Exception:
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=MEMORY")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
            except Exception:
                pass



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_tables_initialized = False
_db_lock = threading.Lock()

def ensure_tables_created():
    global _tables_initialized
    if not _tables_initialized:
        with _db_lock:
            if not _tables_initialized:
                try:
                    backend_dir = os.path.dirname(os.path.abspath(__file__))
                    if backend_dir not in sys.path:
                        sys.path.insert(0, backend_dir)
                    try:
                        import models
                    except ImportError:
                        from . import models
                    try:
                        from seed_data import seed_initial_database
                    except ImportError:
                        from .seed_data import seed_initial_database
                    from sqlalchemy import text
                    models.Base.metadata.create_all(bind=engine)

                    # Ensure new columns exist on learners and assessment_results tables if created from older schema
                    try:
                        with engine.connect() as conn:
                            for col_name, col_type in [
                                ("is_verified", "BOOLEAN DEFAULT 0"),
                                ("verification_code", "VARCHAR"),
                                ("google_id", "VARCHAR"),
                                ("avatar_url", "VARCHAR"),
                                ("has_completed_placement_test", "BOOLEAN DEFAULT 0"),
                                ("placement_score", "FLOAT"),
                                ("proficiency_level", "VARCHAR DEFAULT 'Beginner'"),
                                ("predicted_proficiency_score", "FLOAT DEFAULT 0.0"),
                                ("benchmark_level", "VARCHAR DEFAULT 'Emergent Reader'"),
                                ("cefr_level", "VARCHAR DEFAULT 'A0'"),
                                ("learning_goal", "VARCHAR DEFAULT 'conversation'"),
                                ("prior_knowledge", "VARCHAR DEFAULT 'complete_beginner'"),
                                ("daily_minutes_goal", "INTEGER DEFAULT 15")
                            ]:
                                try:
                                    conn.execute(text(f"ALTER TABLE learners ADD COLUMN {col_name} {col_type}"))
                                    conn.commit()
                                except Exception:
                                    pass

                            for col_name, col_type in [
                                ("cefr_level", "VARCHAR"),
                                ("skill_breakdown", "TEXT"),
                                ("strengths", "TEXT"),
                                ("weak_areas", "TEXT")
                            ]:
                                try:
                                    conn.execute(text(f"ALTER TABLE assessment_results ADD COLUMN {col_name} {col_type}"))
                                    conn.commit()
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    db = SessionLocal()
                    try:
                        seed_initial_database(db)
                    except Exception as se:
                        print(f"[WARN] Seed exception in ensure_tables_created: {se}")
                    finally:
                        db.close()
                    _tables_initialized = True
                except Exception as e:
                    print(f"[WARN] Table creation check warning: {e}")


def get_db():
    ensure_tables_created()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
