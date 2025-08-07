import os

APP_NAME = "intent-classifier"
APP_VERSION = "0.1.0"

DEBUG = os.getenv("SABER_DEBUG", "false").lower() in ("true", "1", "yes")

# API settings
API_HOST = os.getenv("SABER_API_HOST", "0.0.0.0")
API_PORT = os.getenv("SABER_API_PORT", 8005)
API_KEY = os.environ["SABER_API_KEY"]  # required

# Database settings
DATABASE_URL = os.getenv("SABER_DATABASE_URL", "sqlite:///./intent_classifier.db")

# Queue settings
QUEUE_TYPE = os.getenv("SABER_QUEUE_TYPE", "memory")  # Options: memory, redis

# Result Store settings
RESULT_STORE_TYPE = os.getenv(
    "SABER_RESULT_STORE_TYPE", "memory"
)  # Options: memory, redis
RESULT_STORE_TTL = os.getenv(
    "SABER_RESULT_STORE_TTL", 3600
)  # Default TTL in seconds (1 hour)

# Logging settings
LOG_LEVEL = os.getenv("SABER_LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "SABER_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Middleware settings
ALLOWED_HOSTS = os.getenv("SABER_ALLOWED_HOSTS", "*").split(",")

# External settings
CALLBACK_API_KEY = os.getenv("SABER_CALLBACK_API_KEY")