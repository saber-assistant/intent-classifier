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


def load_module(path: str):
    module = importlib.import_module(path)

    return {
        k: getattr(module, k)
        for k in dir(module)
        if k.isupper() and not k.startswith("_")
    }


conf = SimpleNamespace(**load_module("config.settings"))
processors = SimpleNamespace(**load_module("config.processors"))

for k in ["CLASSIFICATION_LAYERS", "INTENT_SEPARATORS"]:
    if k in processors.__dict__:
        for item in processors.__dict__[k]:
            item_module = importlib.import_module(item["path"])
            item["instance"] = item_module(**item["factory"]())
            

__all__ = ["conf", "processors"]
