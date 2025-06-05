"""Observer service for managing Hyperliquid observers."""

import asyncio
import logging
import threading
import uuid
from typing import Dict, Optional
from dataclasses import dataclass

from src.generic.observer import HyperliquidObserver
from src.generic.algo import Algo


logger = logging.getLogger(__name__)


@dataclass
class ObserverInstance:
    """Represents a running observer instance."""
    
    observer_id: str
    address: str
    algo_type: str
    observer: HyperliquidObserver
    thread: threading.Thread
    status: str = "running"


class ObserverService:
    """Service for managing multiple Hyperliquid observers."""
    
    def __init__(self) -> None:
        """Initialize the observer service."""
        self._observers: Dict[str, ObserverInstance] = {}
        self._lock = threading.Lock()
    
    def start_observer(self, address: str, algo_type: str = "default") -> str:
        """Start a new observer for the given address.
        
        Args:
            address: The Hyperliquid address to observe.
            algo_type: The type of algorithm to use.
            
        Returns:
            str: The observer instance ID.
            
        Raises:
            ValueError: If an observer for this address is already running.
        """
        with self._lock:
            # Check if observer already exists for this address
            for instance in self._observers.values():
                if instance.address == address and instance.status == "running":
                    raise ValueError(f"Observer already running for address {address}")
            
            # Create new observer instance
            observer_id = str(uuid.uuid4())
            
            try:
                # Create algorithm instance (you may want to use a factory here)
                algo = self._create_algo(algo_type)
                
                # Create observer
                observer = HyperliquidObserver(address=address, algo=algo)
                
                # Create and start thread
                thread = threading.Thread(
                    target=self._run_observer,
                    args=(observer_id, observer),
                    daemon=True,
                    name=f"Observer-{observer_id[:8]}"
                )
                
                # Store instance
                instance = ObserverInstance(
                    observer_id=observer_id,
                    address=address,
                    algo_type=algo_type,
                    observer=observer,
                    thread=thread,
                    status="running"
                )
                self._observers[observer_id] = instance
                
                # Start the thread
                thread.start()
                
                logger.info(f"Started observer {observer_id} for address {address}")
                return observer_id
                
            except Exception as e:
                logger.error(f"Failed to start observer for {address}: {e}")
                # Clean up if something went wrong
                if observer_id in self._observers:
                    del self._observers[observer_id]
                raise
    
    def stop_observer(self, observer_id: str) -> bool:
        """Stop an observer instance.
        
        Args:
            observer_id: The observer instance ID to stop.
            
        Returns:
            bool: True if the observer was stopped, False if not found.
        """
        with self._lock:
            instance = self._observers.get(observer_id)
            if not instance:
                return False
            
            try:
                # Stop the observer
                instance.observer.stop()
                instance.status = "stopped"
                
                logger.info(f"Stopped observer {observer_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error stopping observer {observer_id}: {e}")
                return False
    
    def get_observer_status(self, observer_id: str) -> Optional[ObserverInstance]:
        """Get the status of an observer instance.
        
        Args:
            observer_id: The observer instance ID.
            
        Returns:
            Optional[ObserverInstance]: The observer instance or None if not found.
        """
        with self._lock:
            return self._observers.get(observer_id)
    
    def list_observers(self) -> Dict[str, ObserverInstance]:
        """List all observer instances.
        
        Returns:
            Dict[str, ObserverInstance]: Dictionary of all observer instances.
        """
        with self._lock:
            return self._observers.copy()
    
    def get_active_count(self) -> int:
        """Get the number of active observers.
        
        Returns:
            int: Number of running observers.
        """
        with self._lock:
            return sum(1 for instance in self._observers.values() 
                      if instance.status == "running")
    
    def stop_all_observers(self) -> None:
        """Stop all running observers."""
        with self._lock:
            for observer_id in list(self._observers.keys()):
                self.stop_observer(observer_id)
    
    def _create_algo(self, algo_type: str) -> Algo:
        """Create an algorithm instance based on type.
        
        Args:
            algo_type: The type of algorithm to create.
            
        Returns:
            Algo: An algorithm instance.
            
        Raises:
            ValueError: If the algorithm type is not supported.
        """
        if algo_type == "default":
            # You'll need to adjust this based on your Algo constructor
            # For now, using placeholder values
            return Algo(symbol="BTC", marginCoin="USDC")
        else:
            raise ValueError(f"Unsupported algorithm type: {algo_type}")
    
    def _run_observer(self, observer_id: str, observer: HyperliquidObserver) -> None:
        """Run an observer in a separate thread.
        
        Args:
            observer_id: The observer instance ID.
            observer: The observer instance to run.
        """
        try:
            logger.info(f"Starting observer thread for {observer_id}")
            observer.start()
        except Exception as e:
            logger.error(f"Observer {observer_id} crashed: {e}")
            # Update status
            with self._lock:
                if observer_id in self._observers:
                    self._observers[observer_id].status = "crashed"


# Global service instance
observer_service = ObserverService() 