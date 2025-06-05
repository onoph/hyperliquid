"""Main FastAPI application for the Hyperliquid Observer API."""

import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from src.api.auth import authenticate_user
from src.api.models import (
    ObserverStartRequest,
    ObserverResponse,
    ObserverStatusResponse,
    HealthResponse
)
from src.api.service import observer_service, ObserverInstance


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Hyperliquid Observer API")
    yield
    # Shutdown
    logger.info("Shutting down Hyperliquid Observer API")
    observer_service.stop_all_observers()


app = FastAPI(
    title="Hyperliquid Observer API",
    description="REST API for managing Hyperliquid WebSocket observers",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        HealthResponse: API health status and active observer count.
    """
    active_count = observer_service.get_active_count()
    return HealthResponse(
        status="healthy",
        active_observers=active_count
    )


@app.post("/observers/start", response_model=ObserverResponse)
async def start_observer(
    request: ObserverStartRequest,
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Start a new observer for the specified address.
    
    Args:
        request: Observer start request with address and algorithm type.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status and observer ID.
        
    Raises:
        HTTPException: If the observer fails to start.
    """
    try:
        observer_id = observer_service.start_observer(
            address=request.address,
            algo_type=request.algo_type
        )
        
        logger.info(f"User {user} started observer {observer_id} for {request.address}")
        
        return ObserverResponse(
            success=True,
            message=f"Observer started successfully for address {request.address}",
            observer_id=observer_id
        )
    
    except ValueError as e:
        # Observer already running for this address
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start observer for {request.address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start observer: {str(e)}"
        )


@app.post("/observers/{observer_id}/stop", response_model=ObserverResponse)
async def stop_observer(
    observer_id: str,
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Stop an observer instance.
    
    Args:
        observer_id: The ID of the observer to stop.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status.
        
    Raises:
        HTTPException: If the observer is not found.
    """
    success = observer_service.stop_observer(observer_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observer {observer_id} not found"
        )
    
    logger.info(f"User {user} stopped observer {observer_id}")
    
    return ObserverResponse(
        success=True,
        message=f"Observer {observer_id} stopped successfully"
    )


@app.get("/observers/{observer_id}/status", response_model=ObserverStatusResponse)
async def get_observer_status(
    observer_id: str,
    user: str = Depends(authenticate_user)
) -> ObserverStatusResponse:
    """Get the status of a specific observer.
    
    Args:
        observer_id: The ID of the observer.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverStatusResponse: Observer status information.
        
    Raises:
        HTTPException: If the observer is not found.
    """
    instance = observer_service.get_observer_status(observer_id)
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observer {observer_id} not found"
        )
    
    return ObserverStatusResponse(
        observer_id=instance.observer_id,
        address=instance.address,
        status=instance.status,
        algo_type=instance.algo_type
    )


@app.get("/observers", response_model=List[ObserverStatusResponse])
async def list_observers(
    user: str = Depends(authenticate_user)
) -> List[ObserverStatusResponse]:
    """List all observer instances.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        List[ObserverStatusResponse]: List of all observer instances.
    """
    observers = observer_service.list_observers()
    
    return [
        ObserverStatusResponse(
            observer_id=instance.observer_id,
            address=instance.address,
            status=instance.status,
            algo_type=instance.algo_type
        )
        for instance in observers.values()
    ]


@app.post("/observers/stop-all", response_model=ObserverResponse)
async def stop_all_observers(
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Stop all running observers.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status.
    """
    observer_service.stop_all_observers()
    
    logger.info(f"User {user} stopped all observers")
    
    return ObserverResponse(
        success=True,
        message="All observers stopped successfully"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions.
    
    Args:
        request: The HTTP request.
        exc: The unhandled exception.
        
    Returns:
        JSONResponse: Error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 