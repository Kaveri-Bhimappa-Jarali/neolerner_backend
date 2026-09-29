import os
import sys
import shutil
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

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

def get_db_url():
    """Retrieve database URL from environment variable DATABASE_URL (or fallback DBURL / DB_URL)."""
    return os.getenv("DATABASE_URL") or os.getenv("DBURL") or os.getenv("DB_URL")

raw_env_url = get_db_url()

if IS_SERVERLESS_OR_READONLY and not raw_env_url:
    print("[CRITICAL PERSISTENCE WARNING] Running in serverless environment without persistent DATABASE_URL environment variable.")
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
SQLALCHEMY_DATABASE_URL = raw_env_url if raw_env_url else f"sqlite:///{normalized_db_path}"

# Standardize postgres scheme for SQLAlchemy 1.4/2.0 compatibility and pure-python pg8000 driver
if raw_env_url and "postgres" in raw_env_url.lower():
    scheme_end = raw_env_url.find("://")
    if scheme_end != -1:
        SQLALCHEMY_DATABASE_URL = "postgresql+pg8000://" + raw_env_url[scheme_end + 3:]
    else:
        SQLALCHEMY_DATABASE_URL = raw_env_url
elif SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# Ensure Supabase pooler username includes project tenant ID if missing
if "pooler.supabase.com" in SQLALCHEMY_DATABASE_URL and "uqczqaycmdltsjfpexlb" not in SQLALCHEMY_DATABASE_URL.split("@")[0]:
    if "://postgres:" in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("://postgres:", "://postgres.uqczqaycmdltsjfpexlb:", 1)


# Configure connection parameters for SQLite vs PostgreSQL
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
is_pg8000 = "pg8000" in SQLALCHEMY_DATABASE_URL

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 30}
elif is_pg8000:
    try:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl_context": ssl_ctx, "timeout": 10}
    except Exception:
        connect_args = {"timeout": 10}

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

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        **engine_kwargs
    )
except Exception as e:
    print(f"[WARN] Primary database engine creation with kwargs failed ({e}). Retrying standard engine creation...")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    except Exception as inner_e:
        print(f"[WARN] Database engine creation failed ({inner_e}). Falling back to SQLite.")
        fallback_uri = f"sqlite:///{normalized_db_path}" if os.path.exists(normalized_db_path) else "sqlite:///:memory:"
        engine = create_engine(
            fallback_uri,
            connect_args={"check_same_thread": False, "timeout": 30}
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
    if _tables_initialized:
        return

    with _db_lock:
        if _tables_initialized:
            return

        try:
            from sqlalchemy import inspect, text
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

            # Fast check: If database tables already exist, skip expensive create_all and seeding round-trips
            tables_exist = False
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1 FROM languages LIMIT 1;"))
                    tables_exist = True
            except Exception:
                tables_exist = False

            if not tables_exist:
                print("[INFO] Creating database schema and seeding initial dataset...")
                models.Base.metadata.create_all(bind=engine)
                db = SessionLocal()
                try:
                    seed_initial_database(db)
                except Exception as se:
                    print(f"[WARN] Seed exception in ensure_tables_created: {se}")
                finally:
                    db.close()

            # Safely verify and add any missing columns for database schema migrations
            try:
                inspector = inspect(engine)
                if inspector.has_table("learners"):
                    existing_learner_cols = {c["name"] for c in inspector.get_columns("learners")}
                    learner_columns_to_check = [
                        ("is_verified", "BOOLEAN DEFAULT FALSE"),
                        ("verification_code", "VARCHAR"),
                        ("google_id", "VARCHAR"),
                        ("avatar_url", "VARCHAR"),
                        ("has_completed_placement_test", "BOOLEAN DEFAULT FALSE"),
                        ("placement_score", "FLOAT"),
                        ("proficiency_level", "VARCHAR DEFAULT 'Beginner'"),
                        ("predicted_proficiency_score", "FLOAT DEFAULT 0.0"),
                        ("benchmark_level", "VARCHAR DEFAULT 'Emergent Reader'"),
                        ("cefr_level", "VARCHAR DEFAULT 'A0'"),
                        ("learning_goal", "VARCHAR DEFAULT 'conversation'"),
                        ("prior_knowledge", "VARCHAR DEFAULT 'complete_beginner'"),
                        ("daily_minutes_goal", "INTEGER DEFAULT 15")
                    ]
                    with engine.connect() as conn:
                        for col_name, col_type in learner_columns_to_check:
                            if col_name not in existing_learner_cols:
                                try:
                                    conn.execute(text(f"ALTER TABLE learners ADD COLUMN {col_name} {col_type}"))
                                    conn.commit()
                                except Exception as alter_err:
                                    print(f"[WARN] Failed adding column {col_name} to learners: {alter_err}")

                if inspector.has_table("assessment_results"):
                    existing_result_cols = {c["name"] for c in inspector.get_columns("assessment_results")}
                    result_columns_to_check = [
                        ("cefr_level", "VARCHAR"),
                        ("skill_breakdown", "TEXT"),
                        ("strengths", "TEXT"),
                        ("weak_areas", "TEXT")
                    ]
                    with engine.connect() as conn:
                        for col_name, col_type in result_columns_to_check:
                            if col_name not in existing_result_cols:
                                try:
                                    conn.execute(text(f"ALTER TABLE assessment_results ADD COLUMN {col_name} {col_type}"))
                                    conn.commit()
                                except Exception as alter_err:
                                    print(f"[WARN] Failed adding column {col_name} to assessment_results: {alter_err}")
            except Exception as schema_err:
                print(f"[WARN] Column migration check exception: {schema_err}")

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
