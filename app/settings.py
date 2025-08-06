"""
Settings loader that provides Django-like configuration management.
This module handles the complexity of dynaconf and environment detection,
exposing a clean interface for the application.
"""

import os
import importlib
from pathlib import Path
from typing import Any, Dict
from dynaconf import Dynaconf


class Settings:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_settings()
            self._initialized = True
    
    def _get_environment(self) -> str:
        """Determine the current environment."""
        return (
            os.getenv("SABER_ENVIRONMENT") or 
            os.getenv("ENVIRONMENT") or 
            os.getenv("ENV") or
            "development"
        ).lower()
    
    def _load_settings(self):
        """Load settings from the appropriate environment file."""
        self.ENVIRONMENT = self._get_environment()
        
        # Define the base directory (project root)
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        
        # Import the appropriate settings module
        try:
            settings_module = f"config.settings.{self.ENVIRONMENT}"
            module = importlib.import_module(settings_module)
            
            # Copy all uppercase attributes from the module to this instance
            for attr in dir(module):
                if attr.isupper():
                    setattr(self, attr, getattr(module, attr))
                    
        except ImportError:
            raise ImportError(
                f"Could not import settings module '{settings_module}'. "
                f"Make sure config/settings/{self.ENVIRONMENT}.py exists."
            )
        
        # Initialize dynaconf for environment variable overrides
        self._setup_dynaconf()
    
    def _setup_dynaconf(self):
        """Setup dynaconf to allow environment variable overrides."""
        env_files = [
            self.BASE_DIR / "envs" / self.ENVIRONMENT / "app.env",
            self.BASE_DIR / ".env",
        ]
        
        self._dynaconf = Dynaconf(
            envvar_prefix="SABER",
            environments=True,
            load_dotenv=True,
            settings_files=env_files,
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value with environment variable override support.
        
        Order of precedence:
        1. Environment variables (with SABER_IC_ prefix)
        2. Settings from the environment-specific file
        3. Default value
        """
        # First check if dynaconf has an override
        dynaconf_value = self._dynaconf.get(key.lower())
        if dynaconf_value is not None:
            return dynaconf_value
            
        # Then check if we have it as an attribute
        if hasattr(self, key):
            return getattr(self, key)
            
        # Finally return the default
        return default
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access for settings."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self.get(name)
    
    def as_dict(self) -> Dict[str, Any]:
        """Return all settings as a dictionary."""
        settings_dict = {}
        for attr in dir(self):
            if attr.isupper():
                settings_dict[attr] = getattr(self, attr)
        return settings_dict
    
    def reload(self):
        """Reload settings (useful for testing)."""
        self._initialized = False
        self._load_settings()


# Create a singleton instance
settings = Settings()

# For convenience, also expose the instance as conf (Django-style)
conf = settings

__all__ = ["settings", "conf"]
