"""API models for the Hyperliquid Observer REST API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ObserverStartRequest(BaseModel):
    """Request model for starting an observer."""
    
    address: str = Field(..., description="The address to observe")
    algo_type: str = Field(default="basic", description="The algorithm type to use")
    is_test: bool = Field(default=True, description="Whether this is a test environment")
    max_leverage: int = Field(default=40, description="The maximum leverage to use")
    api_key: str = Field(..., description="The API key to use")
    gap: int = Field(default=500, description="The gap to use")


class ObserverResponse(BaseModel):
    """Response model for observer operations."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    observer_id: Optional[str] = Field(None, description="The observer ID if applicable")


class ObserverStatusResponse(BaseModel):
    """Response model for observer status."""
    
    observer_id: str = Field(..., description="The observer ID")
    address: str = Field(..., description="The address being observed")
    algo_type: str = Field(..., description="The algorithm type")
    status: str = Field(..., description="The observer status")
    start_time: str = Field(..., description="When the observer was started")
    last_message_time: Optional[str] = Field(None, description="When the last message was received")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="API health status")
    active_observers: int = Field(..., description="Number of active observers")


class LogLevelRequest(BaseModel):
    """Request model for log level changes."""
    
    level: str = Field(..., description="The log level to set")


class LogLevelResponse(BaseModel):
    """Response model for log level operations."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    current_level: str = Field(..., description="The current log level")


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str = Field(..., description="The session ID")
    start_time: str = Field(..., description="When the session started")
    last_activity: str = Field(..., description="Last activity time")
    total_events: int = Field(..., description="Total number of events")
    unique_symbols: int = Field(..., description="Number of unique symbols")
    event_types_count: int = Field(..., description="Number of different event types")


class SessionsResponse(BaseModel):
    """Response model for sessions list."""
    success: bool = Field(..., description="Whether the operation was successful")
    sessions: List[SessionInfo] = Field(..., description="List of sessions")
    total_sessions: int = Field(..., description="Total number of sessions")


class EventInfo(BaseModel):
    """Model for event information."""
    id: int = Field(..., description="Event ID")
    event_type: str = Field(..., description="Type of event")
    symbol: str = Field(..., description="Trading symbol")
    user_address: str = Field(..., description="User address")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(..., description="Event timestamp")
    oid: Optional[str] = Field(None, description="Order ID if applicable")
    price: Optional[str] = Field(None, description="Price if applicable")
    status: Optional[str] = Field(None, description="Status if applicable")
    created_at: str = Field(..., description="When the event was created")
    data: Dict[str, Any] = Field(..., description="Event data")


class EventsResponse(BaseModel):
    """Response model for events list."""
    success: bool = Field(..., description="Whether the operation was successful")
    events: List[EventInfo] = Field(..., description="List of events")
    total_events: int = Field(..., description="Total number of events returned")
    session_id: Optional[str] = Field(None, description="Session ID filter if applied")
    limit: Optional[int] = Field(None, description="Limit applied if any") 