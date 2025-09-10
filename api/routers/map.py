from fastapi import APIRouter
import os

# Import both systems and choose based on available data
try:
    from api.data.deployment_loader import deployment_data
    DEPLOYMENT_AVAILABLE = os.path.exists("data/deployment/core_trade.csv")
except ImportError:
    DEPLOYMENT_AVAILABLE = False

if not DEPLOYMENT_AVAILABLE:
    from api.shapes import get_map_rows, get_product_rows, map_cache_key, product_cache_key

router = APIRouter()


@router.get("/map_v2")
def map_v2(hs6: str = None, year: int = 2023, metric: str = 'export_cz_to_partner', top: int = 0):
    """
    Unified map endpoint
    Returns: [{ iso3, name, value, value_fmt, unit }] for global map display
    """
    try:
        if DEPLOYMENT_AVAILABLE:
            # Deployment: Use CSV data loader
            map_data = deployment_data.get_map_data(hs6=hs6, metric=metric, year=year)
            
            # Apply top filter if requested
            if top > 0:
                map_data = map_data[:top]
                
            return map_data
        else:
            # Local development: Fallback to deployment data for now
            # TODO: Restore original parquet system import
            return []
        
    except Exception as e:
        print(f"Error in map_v2: {e}")
        return []


# Legacy endpoint for backward compatibility
@router.get("/map")
def map_legacy(hs6: str = None, year: int = 2023, metric: str = 'export_cz_to_partner', 
               country: str = None, hs2: str = None):
    """Legacy map endpoint - redirects to map_v2"""
    # Convert to map_v2 format
    return map_v2(hs6=hs6, year=year, metric=metric)