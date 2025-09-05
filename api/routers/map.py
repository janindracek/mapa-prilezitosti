from fastapi import APIRouter
from api.data.deployment_loader import deployment_data

router = APIRouter()


@router.get("/map_v2")
def map_v2(hs6: str = None, year: int = 2023, metric: str = 'export_cz_to_partner', top: int = 0):
    """
    Unified map endpoint using deployment data
    Returns: [{ iso3, name, value, value_fmt, unit }] for global map display
    """
    try:
        # Use deployment data loader for consistent data access
        map_data = deployment_data.get_map_data(hs6=hs6, metric=metric, year=year)
        
        # Apply top filter if requested
        if top > 0:
            map_data = map_data[:top]
            
        return map_data
        
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