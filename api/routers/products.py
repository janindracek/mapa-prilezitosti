from typing import Optional
from fastapi import APIRouter

from api.services.bars import BarsService
from api.helpers import build_trend
from api.data.serving import serving_data
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
    """Top HS6 products by Czech export value (from the serving layer)."""
    try:
        return serving_data.get_products_data(
            country=country, top=top, year=year or 2023,
            hs2=str(hs2) if hs2 is not None else None,
        )
    except Exception as e:
        print(f"Error in products endpoint: {e}")
        return []


@router.get("/trend")
def trend(hs6: str, years: int = 10):
    """Time series for an HS6 aggregated across partners (both years)."""
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
    """Unified bar-chart endpoint (products | partners | peer_compare)."""
    return bars_service.get_bars(
        mode=mode, hs6=hs6, year=year, country=country,
        peer_group=peer_group, top=top, hs2=hs2,
    )
