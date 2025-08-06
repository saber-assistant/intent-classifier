from .base import *  # noqa: F403

DEBUG = True

API_HOST = "127.0.0.1"

API_PORT = 8005

DATABASE_URL = "sqlite:///./dev_intent_classifier.db"

LOG_LEVEL = "DEBUG"

QUEUE_TYPE = "memory"

ALLOWED_HOSTS = ["*"]
