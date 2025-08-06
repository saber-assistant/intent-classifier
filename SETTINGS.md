# Settings Configuration

This project uses a Django-like settings system that's user-friendly and Docker-volume compatible.

## Structure

```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py           # Base settings inherited by all environments
│   ├── development.py    # Development environment settings
│   ├── production.py     # Production environment settings
│   └── testing.py        # Testing environment settings
├── .secrets.toml         # Sensitive configuration (add to .gitignore)
└── settings.py           # Legacy compatibility (deprecated)

app/
├── settings.py           # Main settings loader
├── queue_store/          # Queue backend implementations
└── result_store/         # Result storage backend implementations
```

## Usage

```python
from app.settings import conf

# Access settings as attributes
print(conf.DEBUG)
print(conf.DATABASE_URL)
print(conf.API_PORT)

# Queue and Result Store settings
print(conf.QUEUE_TYPE)
print(conf.RESULT_STORE_TYPE)
print(conf.RESULT_STORE_TTL)
```

## Key Settings

### Queue Configuration
- `QUEUE_TYPE`: "memory" or "redis"
- `REDIS_URL`: Redis connection URL for queue operations

### Result Store Configuration
- `RESULT_STORE_TYPE`: "memory" or "redis"
- `RESULT_STORE_TTL`: Time-to-live for results in seconds
- `RESULT_STORE_REDIS_URL`: Redis connection URL for result storage (separate from queue)

### API Configuration
- `API_HOST`, `API_PORT`: Server binding
- `API_KEY`: Authentication key for API access
- `API_WORKERS`: Number of worker processes (production)

## Environment Selection

The environment is determined by (in order of precedence):
1. `SABER_ENVIRONMENT` environment variable
2. `ENVIRONMENT` environment variable
3. `ENV` environment variable
4. Defaults to `development`

## Environment Variable Overrides

Any setting can be overridden using environment variables with the `SABER_` prefix:

```bash
# Override the API key
export SABER_API_KEY="your-production-api-key"

# Override result store configuration
export SABER_RESULT_STORE_TYPE="redis"
export SABER_RESULT_STORE_TTL=7200

# Override queue configuration
export SABER_QUEUE_TYPE="redis"
export SABER_REDIS_URL="redis://redis-server:6379/0"
```

## Result Store Backends

### Memory Backend
- Stores results in memory with automatic expiration
- Runs a background cleanup task every 60 seconds
- Suitable for development and testing
- Results are lost on application restart

### Redis Backend
- Stores results in Redis with automatic expiration
- More reliable and persistent than memory
- Suitable for production environments
- Results survive application restarts

## Docker Usage

For Docker deployments, you can:

1. **Use environment variables:**
   ```yaml
   environment:
     - SABER_ENVIRONMENT=production
     - SABER_API_KEY=your-secret-api-key
     - SABER_RESULT_STORE_TYPE=redis
     - SABER_RESULT_STORE_REDIS_URL=redis://redis:6379/1
     - SABER_QUEUE_TYPE=redis
     - SABER_REDIS_URL=redis://redis:6379/0
   ```

2. **Volume mount configuration files:**
   ```yaml
   volumes:
     - ./config:/app/config
   ```

## API Endpoints

The result store is accessible via these API endpoints:

- `GET /result/{task_id}` - Get task result
- `DELETE /result/{task_id}` - Delete task result  
- `GET /result/{task_id}/exists` - Check if result exists

## Adding New Settings

1. Add the setting to `config/settings/base.py` with a sensible default
2. Override in environment-specific files as needed
3. Document any environment variables in this README