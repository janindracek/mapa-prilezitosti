from typing import Optional
from fastapi import APIRouter

from api.services.signals_unified import UnifiedSignalsService

router = APIRouter()
signals_service = UnifiedSignalsService()


@router.get("/signals")
def signals(
    country: str | None = None,
    hs6: str | None = None,
    type: str | None = None,
    method: str | None = "trade_structure",
    limit: int = 10,
):
    """Filtered signals from the single serving layer (M4b)."""
    return signals_service.get_signals_by_methodology(
        country=country or "CZE",
        method=method or "trade_structure",
        hs6=hs6,
        signal_type=type,
        limit=limit,
    )


@router.get("/top_signals")
def top_signals(country: str, year: Optional[int] = None, limit: int = 10):
    """Two-tier signal selection for a country (M5): up to ~10 STRONG signals
    balanced across the 4 live methods; if a country has <5 strong, backfill
    with flagged WEAK (permissive) signals. Selection at request time."""
    cap = min(int(limit), 10) if limit else 10
    return signals_service.select_two_tier(country, strong_cap=cap, min_strong=5)


@router.get("/signals/all")
def signals_all(
    country: str | None = None,
    method: str | None = None,
    type: str | None = None,
    band: str | None = None,
    hs6: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    """Analytics side-tab (M5): lean, filterable, paginated view over the FULL
    signal set (~108k). No per-row peer enrichment (too slow at that scale)."""
    return signals_service.get_all_signals(
        country=country, method=method, signal_type=type, band=band, hs6=hs6,
        page=page, page_size=page_size,
    )


@router.get("/signals/methodologies")
def get_available_methodologies():
    """
    Get all available peer group methodologies with metadata.
    
    Returns:
        List of methodologies with signal counts and descriptions
    """
    return signals_service.get_all_available_methodologies()


@router.get("/signals/comprehensive")  
def get_comprehensive_signals(country: str, hs6: str):
    """
    Get comprehensive signal data for a country-product combination.
    
    Returns data for all methodologies including:
    - Signal details
    - Peer country lists
    - Methodology explanations
    - Chart data
    
    Args:
        country: Target country ISO3 code
        hs6: Product code
    """
    return signals_service.get_signals_for_country_product(country, hs6)