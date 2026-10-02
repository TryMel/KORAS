import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_idempotency_key() -> str:
    return f"koras_idemp_{uuid.uuid4().hex}"

def sanitize_untrusted_input(text: str) -> str:
    """
    Section 25: Untrusted input sanitization.
    Treats messages, OCR, web text as DATA, neutralizing prompt injection tokens.
    """
    if not text:
        return ""
    # Strip dangerous systemic prefix patterns that try to override system prompts
    suspicious_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?",
        r"(?i)system\s*:\s*",
        r"(?i)developer\s*mode",
        r"(?i)you\s+are\s+now\s+in\s+unrestricted\s+mode",
        r"(?i)transf[eè]re\s+tout\s+l['\s]argent",
    ]
    cleaned = text
    for pattern in suspicious_patterns:
        cleaned = re.sub(pattern, "[FILTERED_SUSPICIOUS_PROMPT]", cleaned)
    return cleaned.strip()
