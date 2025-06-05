"""API models for the Hyperliquid Observer REST API."""

from typing import Optional
from pydantic import BaseModel, Field


class ObserverStartRequest(BaseModel):
    """Request model for starting an observer."""
    
    address: str = Field(..., description="The Hyperliquid address to observe")
    algo_type: str = Field(default="default", description="Type of algorithm to use")


class ObserverResponse(BaseModel):
    """Response model for observer operations."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    observer_id: Optional[str] = Field(None, description="Observer instance ID")


class ObserverStatusResponse(BaseModel):
    """Response model for observer status."""
    
    observer_id: str = Field(..., description="Observer instance ID")
    address: str = Field(..., description="The observed address")
    status: str = Field(..., description="Observer status (running, stopped)")
    algo_type: str = Field(..., description="Algorithm type")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="API health status")
    active_observers: int = Field(..., description="Number of active observers") 