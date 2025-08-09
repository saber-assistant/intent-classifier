import importlib
import httpx

async def send_post_request(url: str, payload: dict, api_key: str = None, timeout: httpx.Timeout = httpx.Timeout(10.0, connect=5.0)) -> None:
    """Send a POST request to the caller's callback URL."""
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["X-Api-Key"] = api_key

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        
        resp.raise_for_status()
def load_module(path: str):
    module = importlib.import_module(path)

    return {
        k: getattr(module, k)
        for k in dir(module)
        if k.isupper() and not k.startswith("_")
    }

def load_class(path: str, factory: dict):
    mod_path, _, attr = path.rpartition(".")
    module = importlib.import_module(mod_path)
    clazz = getattr(module, attr)
    return clazz(**factory)