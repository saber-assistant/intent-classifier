"""
Example of how to use the new settings system in your application.
"""

from app.conf import settings

def main():
    """Example usage of the settings system."""
    
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"API Host: {settings.API_HOST}")
    print(f"API Port: {settings.API_PORT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    
    # You can also use the get() method with defaults
    custom_setting = settings.get("CUSTOM_SETTING", "default_value")
    print(f"Custom Setting: {custom_setting}")
    
    # Environment variables with SABER_IC_ prefix will override settings
    redis_url = settings.get("REDIS_URL", "redis://localhost:6379/0")
    print(f"Redis URL: {redis_url}")

if __name__ == "__main__":
    main()
