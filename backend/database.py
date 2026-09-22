import os
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
    if (
        os.getenv("VERCEL") in ("1", "true", "True", "yes")
        or "VERCEL" in os.environ
        or "VERCEL_ENV" in os.environ
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "LAMBDA_TASK_ROOT" in os.environ
    ):
        return True
    try:
        test_file = os.path.join(BASE_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return False
    except (IOError, OSError, PermissionError):
        return True

IS_SERVERLESS_OR_READONLY = is_readonly_env()

if IS_SERVERLESS_OR_READONLY and not os.getenv("DATABASE_URL"):
    TMP_DB_PATH = "/tmp/literacy.db"
    if not os.path.exists(TMP_DB_PATH) and os.path.exists(ORIGINAL_DB_PATH):
        try:
            shutil.copy2(ORIGINAL_DB_PATH, TMP_DB_PATH)
            print(f"[INFO] Copied seed database to {TMP_DB_PATH}")
        except Exception as e:
            print(f"[WARN] Failed to copy literacy.db to /tmp: {e}")
    DB_PATH = TMP_DB_PATH
else:
    DB_PATH = ORIGINAL_DB_PATH

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Standardize postgres scheme for SQLAlchemy 1.4/2.0 compatibility
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure timeout for SQLite connections to avoid database locked errors
connect_args = {"check_same_thread": False, "timeout": 30} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

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
                    import models
                    from seed_data import seed_initial_database
                    models.Base.metadata.create_all(bind=engine)
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
