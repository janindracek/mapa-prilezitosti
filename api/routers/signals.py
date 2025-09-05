from typing import Optional
from fastapi import APIRouter

from api.services.signals_unified import UnifiedSignalsService
from api.data.deployment_loader import deployment_data

router = APIRouter()
signals_service = UnifiedSignalsService()


@router.get("/signals")
def signals(
    country: str | None = None,
    hs6: str | None = None,
    type: str | None = None,
    method: str | None = None,
    limit: int = 10,
):
    """
    Unified signals endpoint using deployment data
    Returns filtered signals from the deployment dataset
    """
    try:
        # Use deployment data loader for consistent access
        signals_data = deployment_data.get_signals_data(
            country=country, 
            hs6=hs6, 
            type=type,
            limit=limit
        )
        return signals_data
        
    except Exception as e:
        print(f"Error in signals endpoint: {e}")
        return []


@router.get("/signals_unified") 
def signals_unified(
    country: str | None = None,
    hs6: str | None = None,
    type: str | None = None,
    method: str | None = "trade_structure",
    limit: int = 10,
):
    """
    Serve pre-computed signals from comprehensive ETL pipeline.
    
    Args:
        country: Target country (defaults to all countries if not provided)
        hs6: Filter by product code
        type: Filter by signal type
        method: Peer group methodology (geographic, statistical, human, opportunity)
        limit: Maximum signals to return
    """
    # If no country specified, get signals for all methodologies
    if not country:
        return signals_service.get_signals_by_methodology(
            method=method or "trade_structure", 
            hs6=hs6, 
            signal_type=type, 
            limit=limit
        )
    
    # Country-specific signals
    return signals_service.get_signals_by_methodology(
        country=country,
        method=method or "trade_structure",
        hs6=hs6,
        signal_type=type,
        limit=limit
    )


@router.get("/top_signals")
def top_signals(country: str, year: Optional[int] = None, limit: int = 100):
    """
    Serve precomputed top signals (legacy endpoint - redirects to unified service).
    - country: ISO2/ISO3 (normalized to ISO3)
    - year: optional, defaults to latest available in the parquet
    - limit: cap number of returned rows (per endpoint call)
    """
    # Get balanced signals from ALL methodologies for this country
    # Different signal types have completely different intensity scales, 
    # so we need to ensure fair representation rather than just sorting by intensity
    
    final_signals = []
    seen_signals = set()  # Track (partner_iso3, hs6, type) to prevent duplicates
    
    # Allocate signals across all 5 methodologies (3 peer groups + 2 YoY)
    peer_limit = max(1, limit // 5)  # Each peer methodology gets 1/5 of total
    yoy_limit = max(1, (limit - peer_limit * 3) // 2)  # YoY methods split remaining
    
    methods_config = [
        ("human", peer_limit),                           # Human peer gap signals
        ("trade_structure", peer_limit),                 # Trade structure peer gap signals  
        ("opportunity", peer_limit),                     # Opportunity peer gap signals
        ("yoy_export", yoy_limit),                       # YoY export signals  
        ("yoy_share", yoy_limit)                         # YoY share signals
    ]
    
    for method, method_limit in methods_config:
        method_signals = signals_service.get_signals_by_methodology(
            country=country,
            method=method,
            limit=method_limit * 2  # Get extra to account for duplicates
        )
        
        # Filter out duplicates and take top signals from this method
        unique_method_signals = []
        for signal in method_signals:
            signal_key = (
                signal.get('partner_iso3'), 
                signal.get('hs6'), 
                signal.get('type')
            )
            if signal_key not in seen_signals:
                seen_signals.add(signal_key)
                unique_method_signals.append(signal)
                
                if len(unique_method_signals) >= method_limit:
                    break
        
        final_signals.extend(unique_method_signals[:method_limit])
    
    # Fill remaining slots with highest intensity signals across all methods
    remaining_slots = limit - len(final_signals)
    if remaining_slots > 0:
        extra_signals = signals_service.get_signals_by_methodology(
            country=country,
            method="yoy_export",  # Favor YoY export for extra slots
            limit=remaining_slots * 3  # Get extra to account for duplicates
        )
        
        # Filter out duplicates from extra signals
        unique_extra_signals = []
        for signal in extra_signals:
            signal_key = (
                signal.get('partner_iso3'), 
                signal.get('hs6'), 
                signal.get('type')
            )
            if signal_key not in seen_signals:
                seen_signals.add(signal_key)
                unique_extra_signals.append(signal)
                
                if len(unique_extra_signals) >= remaining_slots:
                    break
        
        final_signals.extend(unique_extra_signals[:remaining_slots])
    
    return final_signals[:limit]


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