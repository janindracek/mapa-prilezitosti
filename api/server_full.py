from dotenv import load_dotenv
load_dotenv()

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.server_cors import APP
from api.routers import map, signals, products, insights, metadata, reference

# Include routers
APP.include_router(map.router, tags=["map"])
APP.include_router(signals.router, tags=["signals"])
APP.include_router(products.router, tags=["products"])
APP.include_router(insights.router, tags=["insights"])
APP.include_router(metadata.router, tags=["metadata"])
APP.include_router(reference.router, tags=["reference"])

# Serve static files from built React app (if available)
static_dir = "ui/dist"
if os.path.exists(static_dir):
    APP.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @APP.get("/")
    async def serve_spa():
        """Serve the React SPA"""
        return FileResponse(f"{static_dir}/index.html")
    
    @APP.get("/{path:path}")
    async def serve_spa_routes(path: str):
        """Serve React SPA routes (fallback for client-side routing)"""
        file_path = f"{static_dir}/{path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for SPA routing
        return FileResponse(f"{static_dir}/index.html")

# Expose app for ASGI servers
app = APP