import pandas as pd
from fastapi import APIRouter

import os
from api.settings import settings
from api.insights_text import generate_insights, extract_context

router = APIRouter()


@router.get("/insights")
def get_insights(importer: str, hs6: str, year: int):
    """Generate insights text for a specific importer/hs6/year combination"""
    # Force using local metrics for insights (deployment data doesn't have compatible schema)
    metrics_path = "data/out/metrics_enriched.parquet"
    text = generate_insights(metrics_path, importer, hs6, year)
    return {"insight": text}


@router.get("/insights_data")
def get_insights_data(importer: str, hs6: str, year: int):
    """
    Return structured data for KeyData component.
    Returns the context data needed for UI calculations.
    """
    # Force using local metrics for insights (deployment data doesn't have compatible schema)
    metrics_path = "data/out/metrics_enriched.parquet"
    df = pd.read_parquet(metrics_path, columns=[
        "year", "partner_iso3", "hs6",
        "import_partner_total", "export_cz_to_partner", "export_cz_total_for_hs6"
    ])
    
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