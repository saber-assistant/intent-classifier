
import importlib
import os
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

ENVIRONMENT = (
    os.getenv("SABER_ENVIRONMENT")
    or os.getenv("ENVIRONMENT")
    or os.getenv("ENV")
    or "development"
).lower()

BASE_DIR = Path(__file__).resolve().parents[1]

for env_file in (BASE_DIR / "envs" / f"{ENVIRONMENT}.env", BASE_DIR / ".env"):
    if env_file.exists():
        load_dotenv(env_file, override=False)

settings_module = importlib.import_module("config.settings")

conf_dict = {
    k: getattr(settings_module, k)
    for k in dir(settings_module)
    if k.isupper()
}

conf = SimpleNamespace(**conf_dict)
settings = conf  # i prefer conf as the name personally but keeping both for compat.

__all__ = ["conf", "settings"]
