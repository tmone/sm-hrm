from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Union
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from fastapi import Request

# Load environment variables
load_dotenv()

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = False

# Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hash password
def get_password_hash(password):
    return pwd_context.hash(password)

# Authenticate user
def authenticate_user(username: str, password: str):
    """Authenticate a user with username and password"""
    from sqlalchemy.orm import Session
    from . import models
    from .database import get_db

    # Get database session
    db = next(get_db())

    try:
        # Find user by username
        user = db.query(models.User).filter(models.User.username == username).first()

        # Check if user exists and password is correct
        if not user or not verify_password(password, user.hashed_password):
            return None

        return user
    finally:
        db.close()

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", ACCESS_TOKEN_EXPIRE_MINUTES)))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from token
def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        if username is None:
            return None
        token_data = TokenData(username=username, is_admin=is_admin)
        return token_data
    except JWTError:
        return None

# Get the current user - optional authentication
# This function allows endpoints to work with or without a logged-in user
async def get_current_user_optional(request: Request):
    # Try to get the token from the cookie
    token = request.cookies.get("access_token")

    # Also check Authorization header for token
    if not token and request.headers.get("Authorization"):
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")

    if not token:
        # No token, return None
        return None

    # Try to get the user from the token
    user_data = get_user_from_token(token)
    if not user_data:
        # Invalid token, return None
        return None

    # Return a simplified user object
    # In a real app, you would look up the user in the database
    return {
        "id": user_data.username,
        "username": user_data.username,
        "is_admin": user_data.is_admin
    }

# Get the current user - required authentication
# This function requires a valid token and will raise an exception if not found
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_data = get_user_from_token(token)
    if user_data is None:
        raise credentials_exception

    # In a real application, you would query the database here
    # For now, we'll just create a simple user object based on the token data
    from sqlalchemy.orm import Session
    from . import models
    from .database import get_db

    # Get database session
    db = next(get_db())

    try:
        # Fetch user from database
        user = db.query(models.User).filter(models.User.username == user_data.username).first()

        if not user:
            raise credentials_exception

        # Return user object
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "is_active": user.is_active
        }
    except Exception as e:
        # If database query fails, fall back to basic user object
        return {
            "id": user_data.username,
            "username": user_data.username,
            "email": user_data.username + "@example.com",
            "is_admin": user_data.is_admin,
            "is_active": True,
            "full_name": "User " + user_data.username
        }
    finally:
        db.close()