import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from dotenv import load_dotenv

load_dotenv()

# 1. Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

if not SECRET_KEY or SECRET_KEY in ("poulify_super_secret_key_change_me_in_production", "change_me"):
    raise RuntimeError(
        "SECRET_KEY is missing or still set to the insecure default. "
        "Generate a strong random key and put it in backend/.env, e.g.:\n"
        "  python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# 2. Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Returns a hashed version of the plain-text password.
    Pre-hashes with SHA256 to bypass bcrypt's 72-character limit.
    """
    pre_hashed = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(pre_hashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches the stored hash."""
    pre_hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(pre_hashed, hashed_password)

# 3. Token Generation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates a JWT token for user sessions."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 4. Token Decoding/Verification
def get_user_from_token(token: str):
    """Decodes a JWT token to extract user info (like email)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None