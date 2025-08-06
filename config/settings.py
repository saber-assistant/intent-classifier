from typing import Callable, Dict, List
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
DEFAULT_INTENT_CONFIDENCE_THRESHOLD = float(
    os.getenv("SABER_DEFAULT_INTENT_CONFIDENCE_THRESHOLD", 0.80)
)

LayerSpec = Dict[str, object]


def _regex_factory(
    pattern_file: str, thr_env: str, thr_default: float
) -> Callable[[], Dict]:
    return lambda: {
        "job_cost": 0,
        "pattern_file": pattern_file,
        "threshold": float(os.getenv(thr_env, thr_default)),
    }


# Full canonical list of classification layers
# Each layer is a dict with:
# - alias: unique identifier for the layer
# - path: import path to the layer class
# - factory: callable that returns a dict of parameters for the layer, doesn't complain about missing env vars for unused layers
ALL_CLASSIFICATION_LAYERS: List[LayerSpec] = [
    {
        "alias": "basic_regex",
        "path": "intent_layers.regex.RegexMatcher",
        "factory": lambda: {
            "job_cost": 0,
            "pattern_file": "basic_patterns.yaml"
        },
    },
    {
        "alias": "kitchen_regex",
        "path": "intent_layers.regex.RegexMatcher",
        "factory": lambda: {
            "job_cost": 0,
            "pattern_file": "kitchen_patterns.yaml"
        },
    },
    {
        "alias": "adaptive_db",
        "path": "intent_layers.adaptive_db.AdaptiveDBMatcher",
        "factory": lambda: {
            "job_cost": 1,
            "model": os.getenv("ADAPTIVE_DB_MODEL", "adaptive_db_model"),
            "refresh_secs": int(os.getenv("ADAPTIVE_DB_REFRESH_SECS", 300)),
            "top_k": int(os.getenv("ADAPTIVE_DB_TOP_K", 5)),
        },
    },
    {
        "alias": "local_model",
        "path": "intent_layers.local.LocalClassifier",
        "factory": lambda: {
            "job_cost": 5,
            "weights_path": "models/local_model.pt",
            "device": os.getenv("LOCAL_MODEL_DEVICE", "cpu"),
            "batch_size": 2,
            "confidence_threshold": 0.75,
        },
    },
    {
        "alias": "external_llm",
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
]

# Whitelist (comma-sep aliases)
# Enable all if not specified
_ENABLED_LAYERS = {
    a.strip() for a in os.getenv("ENABLED_LAYERS", "").split(",") if a.strip()
}
_selected = (
    [layer for layer in ALL_CLASSIFICATION_LAYERS if layer["alias"] in _ENABLED_LAYERS]
    if _ENABLED_LAYERS
    else ALL_CLASSIFICATION_LAYERS
)

CLASSIFICATION_LAYERS = [
    {
        "alias": spec["alias"],
        "path": spec["path"],
        **spec["factory"](),  # env-vars evaluated only now
    }
    for spec in _selected
]
