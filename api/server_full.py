from dotenv import load_dotenv
load_dotenv()

from api.server_cors import APP
from api.routers import map, signals, products, insights, metadata, reference

# Include routers
APP.include_router(map.router, tags=["map"])
APP.include_router(signals.router, tags=["signals"])
APP.include_router(products.router, tags=["products"])
APP.include_router(insights.router, tags=["insights"])
APP.include_router(metadata.router, tags=["metadata"])
APP.include_router(reference.router, tags=["reference"])

# Expose app for ASGI servers
app = APP