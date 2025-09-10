from typing import Optional
from fastapi import APIRouter
import os

from api.services.bars import BarsService
from api.helpers import build_trend

# Import both systems and choose based on available data
try:
    from api.data.deployment_loader import deployment_data
    DEPLOYMENT_AVAILABLE = os.path.exists("data/deployment/core_trade.csv")
except ImportError:
    DEPLOYMENT_AVAILABLE = False

if not DEPLOYMENT_AVAILABLE:
    from api.data_access import get_metrics_cached, metrics_mtime_key

router = APIRouter()
bars_service = BarsService()


@router.get("/products")
def product_bars(
    year: Optional[int] = 2023,
    top: int = 10,
    country: Optional[str] = None,
    hs2: Optional[str | int] = None,
):
    """
    Products endpoint using deployment data
    Returns top HS6 products by export value
    """
    try:
        # Use deployment data loader
        products_data = deployment_data.get_products_data(
            country=country, 
            top=top, 
            year=year or 2023
        )
        
        # Apply HS2 filter if specified
        if hs2:
            hs2_str = str(hs2).zfill(2)  # Pad to 2 digits
            products_data = [p for p in products_data if p['id'][:2] == hs2_str]
            
        return products_data
        
    except Exception as e:
        print(f"Error in products endpoint: {e}")
        return []


@router.get("/trend")
def trend(hs6: str, years: int = 10):
    """
    Return time series for selected HS6 aggregated across partners.
    Adds value_fmt and unit for nicer tooltips in UI.
    """
    if DEPLOYMENT_AVAILABLE:
        # Deployment: Use simple CSV data (only 2023 available)
        df = deployment_data.core_trade
        
        try:
            hs6_int = int(hs6.lstrip('0')) if isinstance(hs6, str) else int(hs6)
            hs6_data = df[df['hs6'] == hs6_int]
            
            if len(hs6_data) == 0:
                return {"data": [], "total_export": 0, "status": "no_data"}
            
            total_export = hs6_data['export_cz_to_partner'].sum()
            
            return {
                "data": [{"year": 2023, "export_cz_to_partner": total_export}],
                "total_export": total_export,
                "status": "single_year_only"
            }
        except (ValueError, TypeError):
            return {"data": [], "total_export": 0, "status": "invalid_hs6"}
    else:
        # Local development: Use full parquet system with multi-year data
        df = get_metrics_cached(metrics_mtime_key())
        return build_trend(df, hs6=hs6, years=years)


@router.get("/bars")
def unified_bars(
    mode: str = "products",  # products | partners | peer_compare
    hs6: str = None,
    year: int = None,
    country: str = None,
    peer_group: str = None,
    top: int = 10,
    hs2: str = None,
):
    """
    Unified bar chart endpoint for all bar types.
    
    Modes:
    - products: Top HS6 products by export value
    - partners: Top countries for specific HS6  
    - peer_compare: Partner bars filtered by peer group
    """
    return bars_service.get_bars(
        mode=mode,
        hs6=hs6,
        year=year,
        country=country,
        peer_group=peer_group,
        top=top,
        hs2=hs2
    )


@router.get("/bars_v2")
def bars_v2_legacy(
    hs6: str,
    year: int,
    mode: str = "peer_compare",
    peer_group: str = None,
    country: str = None,
    top: int = 10,
):
    """Legacy endpoint - redirects to unified bars service"""
    return bars_service.get_partner_bars(
        hs6=hs6,
        year=year,
        mode=mode,
        country=country,
        peer_group=peer_group,
        top=top
    )