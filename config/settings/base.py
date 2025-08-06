"""
Base settings for intent-classifier
All environments inherit from these base settings
"""

# Application settings
APP_NAME = "intent-classifier"
APP_VERSION = "0.1.0"
DEBUG = False

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8005
API_WORKERS = 1
API_KEY = "dogs-are-awesome"  # override in production

# Database settings
DATABASE_URL = "sqlite:///./intent_classifier.db"

# Queue settings
QUEUE_TYPE = "memory"  # Options: memory, redis
REDIS_URL = "redis://localhost:6379/0"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Middleware settings
ALLOWED_HOSTS = ["*"]
