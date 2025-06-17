"""Observer service for managing Hyperliquid observers."""

import asyncio
import logging
import threading
import uuid
from typing import Dict, Optional, Any
from dataclasses import dataclass

from src.generic.cctx_api import Dex, DexConfig
from src.generic.observer import HyperliquidObserver
from src.generic.algo import Algo
from src.data.db.sqlite_data_service import SQLiteDataService
from src.generic.config import config


logger = logging.getLogger(__name__)

COIN='USDC'
SYMBOL='BTC'


@dataclass
class ObserverInstance:
    """Represents a running observer instance."""
    
    observer_id: str
    address: str
    testnet: bool
    gap: int
    coin: str
    symbol: str
    algo_type: str
    observer: HyperliquidObserver
    thread: threading.Thread
    status: str = "running"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation without complex objects.
        """
        return {
            "observer_id": self.observer_id,
            "address": self.address,
            "testnet": self.testnet,
            "gap": self.gap,
            "coin": self.coin,
            "symbol": self.symbol,
            "algo_type": self.algo_type,
            "status": self.status,
            "thread_name": self.thread.name if self.thread else None,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }


class ObserverService:
    """Service for managing multiple Hyperliquid observers."""
    
    def __init__(self) -> None:
        """Initialize the observer service."""
        self._observers: Dict[str, ObserverInstance] = {}
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        # Register cleanup on exit
        import atexit
        atexit.register(self._cleanup_on_exit)
    
    def start_observer(self, address: str, is_test: bool, gap: int, api_key: str, max_leverage: int = None, algo_type: str = "default") -> str:
        """Start a new observer for the given address.
        
        Args:
            address: The Hyperliquid address to observe.
            is_test: Whether this is a test environment (defaults to config value).
            algo_type: The type of algorithm to use (defaults to config value).
            
        Returns:
            str: The observer instance ID.
            
        Raises:
            ValueError: If an observer for this address is already running.
        """
        with self._lock:
            self.check_no_observer_for_address_or_fail(address)
            
            try:
                observer_id = 'obs_' + address
                algo = self._create_algo(algo_type, gap, observer_id, DexConfig(symbol=SYMBOL, marginCoin=COIN, isTest=is_test, walletAddress=address, apiKey=api_key), max_leverage)
                algo.recover_previous_state()
                
                websocket_url = config.get_websocket_url(is_test)
                observer = HyperliquidObserver(address=address, observer_id=observer_id, algo=algo, websocket_url=websocket_url)
                
                thread = threading.Thread(
                    target=self._run_observer,
                    args=(observer_id, observer),
                    daemon=True,
                    name=f"Observer-{observer_id}"
                )
                
                # Store instance
                instance = ObserverInstance(
                    observer_id=observer_id,
                    address=address,
                    gap=gap,
                    testnet=is_test,
                    coin=COIN,
                    symbol=SYMBOL,
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
    
    def delete_observer(self, observer_id: str) -> bool:
        """Stop and delete an observer instance completely.
        
        Args:
            observer_id: The observer instance ID to delete.
            
        Returns:
            bool: True if the observer was deleted, False if not found.
        """
        with self._lock:
            instance = self._observers.get(observer_id)
            if not instance:
                return False
            
            try:
                # Stop the observer first
                instance.observer.stop()
                
                # Remove from observers dict
                del self._observers[observer_id]
                
                logger.info(f"Deleted observer {observer_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting observer {observer_id}: {e}")
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
    
    def list_observers_serializable(self) -> Dict[str, Dict[str, Any]]:
        """List all observer instances in a serializable format.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of serializable observer data.
        """
        with self._lock:
            return {
                observer_id: instance.to_dict() 
                for observer_id, instance in self._observers.items()
            }
    
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
            observer_ids = list(self._observers.keys())
            
        logger.info(f"Stopping {len(observer_ids)} observers...")
        
        for observer_id in observer_ids:
            try:
                logger.info(f"Stopping observer {observer_id}")
                self.stop_observer(observer_id)
                logger.info(f"Observer {observer_id} stopped")
            except Exception as e:
                logger.error(f"Error stopping observer {observer_id}: {e}")
                
        # Force cleanup - supprimer tous les observers même s'ils n'ont pas répondu
        with self._lock:
            remaining = list(self._observers.keys())
            if remaining:
                logger.warning(f"Force cleaning {len(remaining)} remaining observers")
                for obs_id in remaining:
                    try:
                        instance = self._observers[obs_id]
                        instance.observer.stop()
                    except:
                        pass
                # Clear all
                self._observers.clear()
                
        logger.info("All observers stopped and cleaned")
    
    def _create_algo(self, algo_type: str, gap: int, session_id: str, dex_config: DexConfig, max_leverage: int) -> Algo:
        if algo_type == "default":
            # Use config values for algorithm creation
            dex = Dex(dex_config)
            data_service = SQLiteDataService(config.db_path)
            return Algo(dex=dex, data_service=data_service, gap=gap, session_id=session_id, max_leverage=max_leverage)
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
            
            # L'observer.start() ne devrait jamais se terminer normalement
            # Si on arrive ici, c'est qu'il y a eu un problème
            logger.warning(f"Observer {observer_id} start() method returned unexpectedly")
            
        except Exception as e:
            logger.error(f"Observer {observer_id} crashed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update status
            with self._lock:
                if observer_id in self._observers:
                    self._observers[observer_id].status = "crashed"
        finally:
            logger.info(f"Observer thread {observer_id} terminating")
            # Ensure cleanup
            try:
                observer.stop()
            except Exception as e:
                logger.error(f"Error stopping observer {observer_id}: {e}")


    def check_no_observer_for_address_or_fail(self, address: str): 
        for instance in self._observers.values():
                if instance.address == address and instance.status == "running":
                    raise ValueError(f"Observer already running for address {address}")
    
    def _cleanup_on_exit(self) -> None:
        """Force cleanup when program exits."""
        logger.info("Program terminating - stopping all observers")
        self._shutdown_event.set()
        self.stop_all_observers()
        
        # Wait briefly for threads to terminate
        import time
        time.sleep(1)
        
        # Force kill any remaining threads
        for instance in self._observers.values():
            if instance.thread and instance.thread.is_alive():
                logger.warning(f"Force terminating observer {instance.observer_id}")

# Global service instance
observer_service = ObserverService() 