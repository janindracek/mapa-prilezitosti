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
    return {"status": "ok"}
