"""
Password hashing utilities using bcrypt and JWT token generation.

Provides secure password hashing, verification functions, and JWT handling.
"""
import bcrypt
from datetime import datetime, timedelta
from jose import jwt
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plain-text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty or invalid
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    
    # bcrypt generates a random salt and includes it in the hash
    # Default cost factor is 12, which is secure and reasonably fast
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.
    
    Args:
        password: Plain-text password to verify
        password_hash: Bcrypt hash to verify against
        
    Returns:
        True if password matches hash, False otherwise
        
    Raises:
        ValueError: If either parameter is invalid
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    if not password_hash or not isinstance(password_hash, str):
        raise ValueError("Password hash must be a non-empty string")
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ValueError:
        # Invalid hash format
        return False
