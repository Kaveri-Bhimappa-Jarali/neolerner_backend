import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def get_password_hash(password: str) -> str:
    """Hash password supporting both bcrypt and standard library hashlib fallback for serverless."""
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        print(f"[WARN] bcrypt hashing failed, falling back to pbkdf2_sha256: {e}")
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return f"pbkdf2_sha256${salt.hex()}${pwd_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password supporting both bcrypt and pbkdf2_sha256 hashes."""
    if not hashed_password or not plain_password:
        return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            salt = bytes.fromhex(parts[1])
            expected_hash = parts[2]
            computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000).hex()
            return hmac.compare_digest(computed_hash, expected_hash)
        except Exception as e:
            print(f"[WARN] pbkdf2 verification error: {e}")
            return False
    try:
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"[WARN] bcrypt verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

