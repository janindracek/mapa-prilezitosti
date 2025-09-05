from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

APP = FastAPI(title="trade-engine API")

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
    return {
        "status": "debug",
        "working_directory": os.getcwd(),
        "deployment_data_exists": os.path.exists("data/deployment"),
        "csv_files": {
            "core_trade": os.path.exists("data/deployment/core_trade.csv"),
            "signals": os.path.exists("data/deployment/signals_filtered.csv"),
            "countries": os.path.exists("data/deployment/countries.csv")
        }
    }

@APP.get("/")
def root():
    return {"status": "ok"}
