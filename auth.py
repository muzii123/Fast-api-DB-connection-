"""
auth.py

JWT Authentication helpers for the Cart API.

How JWT works in this project:
  1. User registers   → POST /auth/register  → password is hashed & stored in DB
  2. User logs in     → POST /auth/login     → server returns a JWT access token
  3. User calls API   → sends token in header: Authorization: Bearer <token>
  4. Server verifies  → if valid → request goes through, if not → 401 Unauthorized



import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-very-long-random-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")




def hash_password(plain_password: str) -> str:
    """Convert plain text password to bcrypt hash for safe storage in DB."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain text password matches the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)




def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT token.

    The token contains:
     sub: the user's email (subject)
     exp: expiration timestamp
    
    It is signed with SECRET_KEY so the server can verify it wasn't tampered with.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Raises HTTPException 401 if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return {"email": email}
    except JWTError:
        raise credentials_exception




def get_db():
    """Database session dependency (duplicated here to avoid circular imports)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — use this to protect any endpoint.

    Usage:
        @app.get("/protected")
        def my_endpoint(current_user: User = Depends(get_current_user)):
            ...

    What it does:
      1. Extracts token from Authorization: Bearer <token> header
      2. Decodes and verifies the JWT
      3. Looks up the user in the database
      4. Returns the User object — or raises 401 if anything is wrong
    """
    token_data = decode_token(token)
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Token may be stale.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
