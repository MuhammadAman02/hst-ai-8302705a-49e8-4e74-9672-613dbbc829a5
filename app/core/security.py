"""Security and authentication for the fraud detection system"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    roles: list = []
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model for authentication"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: list = []
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[Any, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        roles: list = payload.get("roles", [])
        exp: datetime = datetime.fromtimestamp(payload.get("exp", 0))
        
        if username is None:
            return None
        
        return TokenData(username=username, roles=roles, exp=exp)
    
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def get_current_active_user(token: str) -> Optional[User]:
    """Get current active user from token"""
    token_data = verify_token(token)
    
    if token_data is None:
        return None
    
    # In a real application, you would fetch user data from database
    # For demo purposes, we'll return a mock user
    if token_data.username == "analyst":
        return User(
            username="analyst",
            email="analyst@irishbank.ie",
            full_name="Fraud Analyst",
            roles=["analyst", "investigator"],
            is_active=True
        )
    
    return None


def check_permission(user: User, required_role: str) -> bool:
    """Check if user has required role/permission"""
    return required_role in user.roles or "admin" in user.roles


# Demo users for development (replace with database in production)
DEMO_USERS = {
    "analyst": {
        "username": "analyst",
        "email": "analyst@irishbank.ie",
        "full_name": "Fraud Analyst",
        "hashed_password": get_password_hash("secure123"),
        "roles": ["analyst", "investigator"],
        "is_active": True
    },
    "admin": {
        "username": "admin",
        "email": "admin@irishbank.ie",
        "full_name": "System Administrator",
        "hashed_password": get_password_hash("admin123"),
        "roles": ["admin", "analyst", "investigator"],
        "is_active": True
    }
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password"""
    user_data = DEMO_USERS.get(username)
    
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        roles=user_data["roles"],
        is_active=user_data["is_active"]
    )