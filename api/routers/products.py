from typing import Optional
from fastapi import APIRouter

from api.services.bars import BarsService
from api.helpers import build_trend
from api.data_access import get_metrics_cached, metrics_mtime_key

router = APIRouter()
bars_service = BarsService()


@router.get("/products")
def product_bars(
    year: Optional[int] = None,
    top: int = 10,
    country: Optional[str] = None,
    hs2: Optional[str | int] = None,
):
    """
    Product bars with optional country/HS2 filters.
    - Without filters: top HS6 by CZ exports for the year.
    - With country: top HS6 only to that partner.
    - With hs2: restrict candidates to that 2-digit chapter.
    """
    return bars_service.get_product_bars(year=year, top=top, country=country, hs2=str(hs2) if hs2 else None)


@router.get("/trend")
def trend(hs6: str, years: int = 10):
    """
    Return time series for selected HS6 aggregated across partners.
    Adds value_fmt and unit for nicer tooltips in UI.
    """
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