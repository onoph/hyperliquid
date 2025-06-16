"""Simple configuration manager for environment variables."""

import os
from typing import Optional


class Config:
    """Simple configuration class for environment variables."""
    
    def __init__(self) -> None:
        """Load configuration from environment variables."""
        # Database
        self.db_path: str = os.getenv("DB_PATH", "data/observations.db")
        
        # Observer settings
        self.max_observers: int = int(os.getenv("MAX_OBSERVERS", "10"))
        
        # API settings
        self.testnet_url: str = os.getenv("TESTNET_URL")
        self.mainnet_url: str = os.getenv("MAINNET_URL")

    def get_websocket_url(self, is_test: bool) -> str:
        if is_test:
            return self.testnet_url
        else:
            return self.mainnet_url


# Global config instance
config = Config()