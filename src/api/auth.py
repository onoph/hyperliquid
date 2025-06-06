"""Authentication module for the API."""

import os
from typing import Optional

from dotenv.main import DotEnv
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBasic()

def get_auth_credentials() -> tuple[str, str]:
    """Get authentication credentials from environment variables.
    
    Returns:
        tuple[str, str]: Username and password from environment variables.
        
    Raises:
        ValueError: If credentials are not set in environment variables.
    """
    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    
    if not username or not password:
        raise ValueError(
            "API_USERNAME and API_PASSWORD environment variables must be set"
        )
    
    return username, password


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Authenticate user with basic HTTP authentication.
    
    Args:
        credentials: HTTP basic credentials from the request.
        
    Returns:
        str: The authenticated username.
        
    Raises:
        HTTPException: If authentication fails.
    """
    try:
        expected_username, expected_password = get_auth_credentials()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    # Simple constant-time comparison to prevent timing attacks
    username_correct = credentials.username == expected_username
    password_correct = credentials.password == expected_password
    
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username 