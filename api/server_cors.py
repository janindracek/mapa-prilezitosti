import json
import math

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def _json_clean(o):
    """Recursively make a payload JSON-safe: NaN/Inf -> null, numpy scalars -> py."""
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {k: _json_clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_clean(v) for v in o]
    if hasattr(o, "item"):  # numpy scalar
        return _json_clean(o.item())
    return o


class SafeJSONResponse(JSONResponse):
    """JSON responses where NaN/Inf serialize as null (Starlette's default
    allow_nan=False otherwise 500s on the NaN cells in our signal data)."""
    def render(self, content) -> bytes:
        return json.dumps(_json_clean(content), ensure_ascii=False, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")


APP = FastAPI(title="trade-engine API", default_response_class=SafeJSONResponse)

# GZip compression (must be added first to wrap all responses)
APP.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Good balance of compression vs CPU (1-9, 6 is default)
)

# CORS (browsers)
APP.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],         # tighten later (e.g., http://localhost:5173)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@APP.get("/health")
def health():
    return {"status": "ok", "message": "API server is running"}

@APP.get("/debug")
def debug():
    import os
    serving = "data/serving"
    return {
        "status": "debug",
        "working_directory": os.getcwd(),
        "serving_dir_exists": os.path.isdir(serving),
        "serving_files": sorted(os.listdir(serving)) if os.path.isdir(serving) else [],
        "config_yaml_exists": os.path.exists("data/config.yaml"),
    }

@APP.get("/")
def root():
    return {"status": "ok"}
