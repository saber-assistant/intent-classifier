"""
Example of integrating the new settings system with the existing API.
This shows how to modify app/api.py to use the new settings.
"""

import logging
from fastapi import FastAPI
from app.conf import settings

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

logger = logging.getLogger(settings.APP_NAME)

# Create FastAPI app with settings
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Example of using settings in the app
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }

@app.get("/config")
def get_config():
    """Return non-sensitive configuration for debugging."""
    return {
        "environment": settings.ENVIRONMENT,
        "api_host": settings.API_HOST,
        "api_port": settings.API_PORT,
        "debug": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
        "queue_type": settings.QUEUE_TYPE,
        # Don't expose sensitive settings like SECRET_KEY or DATABASE_URL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "example_api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=settings.DEBUG,
    )
