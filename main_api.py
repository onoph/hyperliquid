"""Main FastAPI application for the Hyperliquid Observer API."""

import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from src.api.auth import authenticate_user
from src.api.models import (
    ObserverStartRequest,
    ObserverResponse,
    ObserverStatusResponse,
    HealthResponse,
    LogLevelRequest,
    LogLevelResponse,
    SessionsResponse,
    SessionInfo,
    EventsResponse,
    EventInfo
)
from src.api.service import observer_service, ObserverInstance
from src.data.db.sqlite_data_service import SQLiteDataService
import json
import atexit

# Triple protection - atexit hook au niveau global
def cleanup_on_exit():
    """Cleanup function appelée à la fermeture du programme."""
    logger.info("Program exit detected - stopping all observers (atexit)")
    try:
        observer_service.stop_all_observers()
    except Exception as e:
        logger.error(f"Error during atexit cleanup: {e}")

atexit.register(cleanup_on_exit)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Valid log levels
VALID_LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Database instance
db_service = SQLiteDataService("data/observations.db")


def get_current_log_level() -> str:
    """Get the current root logger level as a string."""
    root_logger = logging.getLogger()
    level = root_logger.getEffectiveLevel()
    
    # Convert numeric level back to string
    for level_name, level_value in VALID_LOG_LEVELS.items():
        if level_value == level:
            return level_name
    return f"UNKNOWN({level})"


def set_log_level(level_name: str) -> bool:
    """Set the log level for all loggers.
    
    Args:
        level_name: The log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        bool: True if the level was set successfully, False otherwise.
    """
    level_name = level_name.upper()
    
    if level_name not in VALID_LOG_LEVELS:
        return False
    
    level = VALID_LOG_LEVELS[level_name]
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Set level for all existing loggers
    for logger_name in logging.Logger.manager.loggerDict:
        existing_logger = logging.getLogger(logger_name)
        existing_logger.setLevel(level)
    
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Hyperliquid Observer API")
    
    try:
        yield
    finally:
        # Shutdown - Cette section SERA toujours appelée même avec Ctrl+C
        logger.info("Shutting down Hyperliquid Observer API - Stopping all observers...")
        observer_service.stop_all_observers()
        
        # Attendre un peu que les observers s'arrêtent
        import asyncio
        await asyncio.sleep(1)
        
        logger.info("All observers stopped - API shutdown complete")


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


@app.get("/logs/level", response_model=LogLevelResponse)
async def get_log_level(
    user: str = Depends(authenticate_user)
) -> LogLevelResponse:
    """Get the current log level.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        LogLevelResponse: Current log level information.
    """
    current_level = get_current_log_level()
    
    return LogLevelResponse(
        success=True,
        message=f"Current log level is {current_level}",
        current_level=current_level
    )


@app.post("/logs/level", response_model=LogLevelResponse)
async def set_log_level_endpoint(
    request: LogLevelRequest,
    user: str = Depends(authenticate_user)
) -> LogLevelResponse:
    """Set the global log level.
    
    Args:
        request: Log level change request.
        user: Authenticated user (from dependency injection).
        
    Returns:
        LogLevelResponse: Response with success status and current level.
        
    Raises:
        HTTPException: If the log level is invalid.
    """
    level_name = request.level.upper()
    
    if level_name not in VALID_LOG_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log level. Valid levels are: {', '.join(VALID_LOG_LEVELS.keys())}"
        )
    
    success = set_log_level(level_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set log level"
        )
    
    logger.info(f"User {user} changed log level to {level_name}")
    
    return LogLevelResponse(
        success=True,
        message=f"Log level successfully changed to {level_name}",
        current_level=level_name
    )


@app.get("/data/sessions", response_model=List[str])
async def get_all_sessions(
    user: str = Depends(authenticate_user)
) -> List[str]:
    """Get all unique sessions from the database.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        List[str]: List of all sessions.
    """
    try:
        session_ids = db_service.get_all_sessions()
        return session_ids
    
    except Exception as e:
        logger.error(f"Error retrieving sessions: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@app.get("/data/events", response_model=EventsResponse)
async def get_all_events(
    user: str = Depends(authenticate_user),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum number of events to return"),
    session_id: Optional[str] = Query(None, description="Filter by session ID")
) -> EventsResponse:
    """Get all events from the database with optional filters.
    
    Args:
        user: Authenticated user (from dependency injection).
        limit: Maximum number of events to return (1-10000).
        session_id: Optional session ID filter.
        
    Returns:
        EventsResponse: List of events with optional filters applied.
    """
    try:
        events_data = db_service.get_observations_by_session(session_id)
        
        events = []
        for event in events_data:
            # Parse the JSON data field
            try:
                data = json.loads(event['data']) if event['data'] else {}
            except json.JSONDecodeError:
                data = {}
            
            events.append(EventInfo(
                id=event['id'],
                event_type=event['event_type'],
                symbol=event['symbol'],
                user_address=event['user_address'],
                session_id=event['session_id'],
                timestamp=event['timestamp'],
                oid=event['oid'],
                price=event['price'],
                status=event['status'],
                created_at=event['created_at'],
                data=data
            ))
        
        logger.info(f"User {user} retrieved {len(events)} events (limit: {limit}, session: {session_id})")
        
        return EventsResponse(
            success=True,
            events=events,
            total_events=len(events),
            session_id=session_id,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Error retrieving events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events"
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
            is_test=request.is_test,
            gap=request.gap,
            max_leverage=request.max_leverage,
            algo_type=request.algo_type,
            api_key=request.api_key
        )
        
        logger.info(f"User {user} started observer {observer_id} for {request.address}")
        
        return ObserverResponse(
            success=True,
            message=f"Observer started successfully for address {request.address}",
            observer_id=observer_id
        )
    
    except Exception as e:
        logger.error(f"Failed to start observer for {request.address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start observer: {str(e)}"
        )


def _handle_observer_action(observer_id: str, user: str, action: str, service_method) -> ObserverResponse:
    """Helper function to handle observer actions (stop/delete).
    
    Args:
        observer_id: The ID of the observer.
        user: The authenticated user.
        action: Action name for logging (e.g., "stop", "delete").
        service_method: The service method to call.
        
    Returns:
        ObserverResponse: Response with success status.
        
    Raises:
        HTTPException: If the observer doesn't exist or action fails.
    """
    try:
        success = service_method(observer_id)
        
        if not success:
            logger.warning(f"Observer {observer_id} not found for {action}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observer {observer_id} not found"
            )
        
        logger.info(f"User {user} {action}ped observer {observer_id}")
        
        return ObserverResponse(
            success=True,
            message=f"Observer {observer_id} {action}ped successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to {action} observer {observer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {action} observer: {str(e)}"
        )


@app.post("/observers/{observer_id}/stop", response_model=ObserverResponse)
async def stop_observer(
    observer_id: str,
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Stop a specific observer.
    
    Args:
        observer_id: The ID of the observer to stop.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status.
        
    Raises:
        HTTPException: If the observer doesn't exist or fails to stop.
    """
    return _handle_observer_action(observer_id, user, "stop", observer_service.stop_observer)


@app.delete("/observers/{observer_id}", response_model=ObserverResponse)
async def delete_observer(
    observer_id: str,
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Delete a specific observer (stop and remove completely).
    
    Args:
        observer_id: The ID of the observer to delete.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status.
        
    Raises:
        HTTPException: If the observer doesn't exist or fails to delete.
    """
    return _handle_observer_action(observer_id, user, "delet", observer_service.delete_observer)


@app.get("/observers/{observer_id}/status", response_model=ObserverStatusResponse)
async def get_observer_status(
    observer_id: str,
    user: str = Depends(authenticate_user)
) -> ObserverStatusResponse:
    """Get the status of a specific observer.
    
    Args:
        observer_id: The ID of the observer to check.
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverStatusResponse: Observer status information.
        
    Raises:
        HTTPException: If the observer doesn't exist.
    """
    try:
        observer_info = observer_service.get_observer_status(observer_id)
        
        if not observer_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observer {observer_id} not found"
            )
        
        return ObserverStatusResponse(
            observer_id=observer_id,
            address=observer_info.address,
            algo_type=observer_info.algo_type,
            status=observer_info.status,
            testnet=observer_info.testnet,
            coin=observer_info.coin,
            symbol=observer_info.symbol
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get observer status for {observer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observer status: {str(e)}"
        )


@app.get("/observers")
async def list_observers(
    user: str = Depends(authenticate_user)
) -> Dict[str, Dict[str, Any]]:
    """List all observers and their status.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of all observer instances.
    """
    try:
        observers = observer_service.list_observers_serializable()
        return observers
    
    except Exception as e:
        logger.error(f"Failed to list observers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list observers: {str(e)}"
        )


@app.post("/observers/stop-all", response_model=ObserverResponse)
async def stop_all_observers(
    user: str = Depends(authenticate_user)
) -> ObserverResponse:
    """Stop all active observers.
    
    Args:
        user: Authenticated user (from dependency injection).
        
    Returns:
        ObserverResponse: Response with success status.
    """
    try:
        observer_service.stop_all_observers()
        count = observer_service.get_active_count()
        
        logger.info(f"User {user} stopped all observers")
        
        return ObserverResponse(
            success=True,
            message=f"All observers stopped successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to stop all observers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop all observers: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions.
    
    Args:
        request: The FastAPI request object.
        exc: The unhandled exception.
        
    Returns:
        JSONResponse: Error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    import signal
    import sys
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, stopping all observers...")
        observer_service.stop_all_observers()
        logger.info("Signal handler finished - exiting")
        sys.exit(0)
    
    # Double protection - handle signals même si uvicorn ne les gère pas correctement
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 