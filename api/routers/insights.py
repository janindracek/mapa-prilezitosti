import pandas as pd
from fastapi import APIRouter

import os
from api.settings import settings
from api.insights_text import generate_insights, extract_context

# Import both systems and choose based on available data
try:
    from api.data.deployment_loader import deployment_data
    DEPLOYMENT_AVAILABLE = os.path.exists("data/deployment/core_trade.csv")
except ImportError:
    DEPLOYMENT_AVAILABLE = False

if not DEPLOYMENT_AVAILABLE:
    from api.data_access import get_metrics_cached, metrics_mtime_key

router = APIRouter()


@router.get("/insights")
def get_insights(importer: str, hs6: str, year: int):
    """Generate insights text for a specific importer/hs6/year combination"""
    if DEPLOYMENT_AVAILABLE:
        # Use deployment data - create a minimal metrics structure for insights
        trade_data = deployment_data.core_trade
        if trade_data.empty:
            return {"insight": "No data available for insights generation"}
        text = generate_insights_from_deployment(trade_data, importer, hs6, year)
    else:
        # Use full local metrics file
        metrics_path = "data/out/metrics_enriched.parquet"
        text = generate_insights(metrics_path, importer, hs6, year)
    return {"insight": text}


@router.get("/insights_data")
def get_insights_data(importer: str, hs6: str, year: int):
    """
    Return structured data for KeyData component.
    Returns the context data needed for UI calculations.
    """
    if DEPLOYMENT_AVAILABLE:
        # Use deployment data
        trade_data = deployment_data.core_trade
        if trade_data.empty:
            return {"error": "No deployment data available"}
        
        # Extract basic data from core_trade for KeyData component
        return extract_context_from_deployment(trade_data, importer, hs6, year)
    else:
        # Use full local metrics file
        metrics_path = "data/out/metrics_enriched.parquet"
        df = pd.read_parquet(metrics_path)
        context = extract_context(df, importer, hs6, year, lookback=5)
        
        return {
            "c_import_total": context.get("imp_last"),           # Country's total imports 
            "cz_share_in_c": context.get("pen_imp"),            # CZ's share of country's imports
            "median_peer_share": context.get("pen_med"),        # Median peer penetration
            "import_yoy_change": context.get("imp_yoy_change"),  # Country's import YoY change %
            "cz_to_c": context.get("cz_to_imp_last"),           # CZ export to this country
            "cz_world_total": context.get("cz_global_last"),    # CZ total export for this HS6
            "cz_delta_pct": context.get("imp_yoy_change")       # YoY change %
        }


def extract_context_from_deployment(trade_data: pd.DataFrame, importer: str, hs6: str, year: int) -> dict:
    """Extract context data from deployment core_trade data for KeyData component"""
    try:
        # Filter data for the specific importer and HS6
        hs6_int = int(hs6.lstrip('0')) if isinstance(hs6, str) else int(hs6)
        filtered_data = trade_data[
            (trade_data['partner_iso3'] == importer) & 
            (trade_data['hs6'] == hs6_int)
        ]
        
        if filtered_data.empty:
            # Return fallback data structure with proper types
            return {
                "c_import_total": 0.0,
                "cz_share_in_c": 0.0,
                "median_peer_share": 0.0,
                "import_yoy_change": 0.0,
                "cz_to_c": 0.0,
                "cz_world_total": 0.0,
                "cz_delta_pct": 0.0
            }
        
        # Extract available metrics from core_trade data
        row = filtered_data.iloc[0]  # Take first row if multiple
        
        # Map deployment data columns to expected KeyData format with proper type conversion
        return {
            "c_import_total": float(row.get('import_partner_total_x', 0) or 0),
            "cz_share_in_c": float(row.get('podil_cz_na_importu', 0) or 0),
            "median_peer_share": 0.0,  # Not available in core_trade
            "import_yoy_change": float(row.get('YoY_export_change', 0) or 0),
            "cz_to_c": float(row.get('export_cz_to_partner', 0) or 0),
            "cz_world_total": float(row.get('export_cz_total_for_hs6', 0) or 0),
            "cz_delta_pct": float(row.get('YoY_export_change', 0) or 0)  # Use YoY as delta
        }
        
    except Exception as e:
        # Return safe fallback on any error with proper types
        return {
            "c_import_total": 0.0,
            "cz_share_in_c": 0.0,
            "median_peer_share": 0.0,
            "import_yoy_change": 0.0,
            "cz_to_c": 0.0,
            "cz_world_total": 0.0,
            "cz_delta_pct": 0.0
        }


def generate_insights_from_deployment(trade_data: pd.DataFrame, importer: str, hs6: str, year: int) -> str:
    """Generate insights text from deployment data"""
    try:
        hs6_int = int(hs6.lstrip('0')) if isinstance(hs6, str) else int(hs6)
        filtered_data = trade_data[
            (trade_data['partner_iso3'] == importer) & 
            (trade_data['hs6'] == hs6_int)
        ]
        
        if filtered_data.empty:
            return f"No trade data available for {importer} and HS6 {hs6} in {year}."
        
        row = filtered_data.iloc[0]
        export_value = row.get('export_cz_to_partner', 0)
        cz_share = row.get('podil_cz_na_importu', 0)
        
        # Generate basic insights text
        if export_value > 1_000_000:
            value_text = f"{export_value/1_000_000:.1f} million USD"
        else:
            value_text = f"{export_value:,.0f} USD"
        
        share_text = f"{cz_share*100:.2f}%" if cz_share < 1 else f"{cz_share:.2f}%"
        
        return f"Czech exports to {importer} for HS6 {hs6}: {value_text}, representing {share_text} market share."
        
    except Exception as e:
        return f"Unable to generate insights: {str(e)}"