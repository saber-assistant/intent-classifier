import os
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

from .utils import load_module, load_class

ENVIRONMENT = (
    os.getenv("SABER_ENVIRONMENT")
    or os.getenv("ENVIRONMENT")
    or os.getenv("ENV")
    or "development"
).lower()

BASE_DIR = Path(__file__).resolve().parent.parent

for env_file in (BASE_DIR / "envs" / f"{ENVIRONMENT}.env", BASE_DIR / ".env"):
    if env_file.exists():
        load_dotenv(env_file, override=False)

conf = SimpleNamespace(**load_module("config.settings"))
processors = SimpleNamespace(**load_module("config.processors"))

for k in ["INTENT_SEPARATORS", "CLASSIFICATION_LAYERS"]:
    if k in processors.__dict__:
        for item in processors.__dict__[k]:
            item["instance"] = load_class(item["path"], item.get("factory", {}))

__all__ = ["conf", "processors"]
