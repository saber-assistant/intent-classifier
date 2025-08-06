import os

APP_NAME = "intent-classifier"
APP_VERSION = "0.1.0"

DEBUG = os.getenv("SABER_DEBUG", "false").lower() in ("true", "1", "yes")

# API settings
API_HOST = os.getenv("SABER_API_HOST", "0.0.0.0")
API_PORT = os.getenv("SABER_API_PORT", 8005)
API_KEY = os.getenv("SABER_API_KEY")  # required

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


# Classification settings
ALL_INTENT_SEPARATOR_MODELS = {
    "local_intent_separator": {
        "path": "intent_separator.local_model.LocalIntentSeparator",
    }
}

INTENT_SEPARATOR_MODEL = ALL_INTENT_SEPARATOR_MODELS[os.getenv("SABER_INTENT_SEPARATOR_MODEL", "local_intent_separator")]


DEFAULT_INTENT_CONFIDENCE_THRESHOLD = float(
    os.getenv("SABER_DEFAULT_INTENT_CONFIDENCE_THRESHOLD", 0.80)
)

# Full canonical list of classification layers
# Each layer is a dict with:
# - key/alias: unique identifier for the layer
# - path: import path to the layer class
# - factory: callable that returns a dict of parameters for the layer, doesn't complain about missing env vars for unused layers
ALL_CLASSIFICATION_LAYERS = {
    "basic_regex": {
        "path": "intent_layers.regex.RegexMatcher",
        "factory": lambda: {
            "job_cost": 0,
            "pattern_file": "basic_patterns.yaml",
        },
    },
    "kitchen_regex": {
        "path": "intent_layers.regex.RegexMatcher",
        "factory": lambda: {
            "job_cost": 0,
            "pattern_file": "kitchen_patterns.yaml",
        },
    },
    "adaptive_db": {
        "path": "intent_layers.adaptive_db.AdaptiveDBMatcher",
        "factory": lambda: {
            "job_cost": 1,
            "model": os.getenv("ADAPTIVE_DB_MODEL", "adaptive_db_model"),
            "refresh_secs": int(os.getenv("ADAPTIVE_DB_REFRESH_SECS", 300)),
            "top_k": int(os.getenv("ADAPTIVE_DB_TOP_K", 5)),
        },
    },
    "local_model": {
        "path": "intent_layers.local_model.LocalModelClassifier",
        "factory": lambda: {
            "job_cost": 5,
            "weights_path": "models/local_model.pt",
            "device": os.getenv("LOCAL_MODEL_DEVICE", "cpu"),
            "batch_size": 2,
            "confidence_threshold": 0.75,
        },
    },
    "external_llm": {
        "path": "intent_layers.external.ExternalLLM",
        "factory": lambda: {
            "job_cost": 9,
            "provider": os.getenv("EXT_MODEL_PROVIDER", "openai"),
            "model": os.getenv("EXT_MODEL_NAME", "gpt-4o-mini"),
            "temperature": float(os.getenv("EXT_MODEL_TEMP", 0.1)),
            "max_tokens": 256,
            "timeout": 30,
        },
    },
}

# Comma-separated whitelist. Enable *all* if empty
_ENABLED = {a.strip() for a in os.getenv("ENABLED_LAYERS", "").split(",") if a.strip()}
_selected_aliases = _ENABLED or ALL_CLASSIFICATION_LAYERS.keys()

# Build ordered list (preserve the declared order in ALL_CLASSIFICATION_LAYERS)
CLASSIFICATION_LAYERS = [
    {
        "alias": alias,
        "path": spec["path"],
        **spec["factory"](),          # factory runs only for enabled aliases
    }
    for alias, spec in ALL_CLASSIFICATION_LAYERS.items()
    if alias in _selected_aliases
]